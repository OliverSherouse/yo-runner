#! /usr/bin/env python3
"""
Yo - a yaml-driven task runner for lazy people
"""

import argparse
import asyncio
import collections
import functools
import logging
import os
import shlex
import signal
import sys

import yaml

from pathlib import Path

log = logging.getLogger(name="yo")
__version__ = "0.1.2"


def error(message):
    """ Give error message and exit"""
    log.error(message)
    sys.exit(1)


def _extract_env_and_vars(parsed):
    """
    Remove and appropriately process "vars" and "env" sections of parsed
    taskfile if present in the first first two sections. Modifies
    **parsed** in place

    If an "env" section exists, add the variables defined in it to the
    environment. If a "vars" section exist, extract them.

    Arguments:

    * **parsed**: a parsed representation of a taskfile

    Returns: a dictionary containing vars defined in **parsed**

    """
    # There has *got* to be a way to do this more simply
    env = os.environ.copy()
    vars = {}
    first = tuple(parsed.keys())[0]
    if first in {"env", "vars"}:
        if first == "env":
            env.update(parsed.pop("env"))
        else:
            vars = parsed.pop("vars")
        second = tuple(parsed.keys())[0]
        if second in {"env", "vars"}:
            if second == "env":
                env.update(parsed.pop("env"))
            else:
                vars = parsed.pop("vars")
    return env, vars


class TaskDefs(dict):
    """
    A dict-like mapping of command names to `Task` objects

    Arguments:

    * **taskfile**: a Path leading to a taskfile
    """

    def __init__(self, taskfile):
        self.taskfile = Path(taskfile)
        parsed = yaml.load(self.taskfile.open(), Loader=yaml.SafeLoader)
        self.env, self.vars = _extract_env_and_vars(parsed)
        self.tasks = self._parse_tasks(parsed)

    def __str__(self):
        """Print available tasks and exit"""
        to_str = ["Available tasks:"]
        to_str.extend(["\t{}".format(task) for task in self.tasks])
        return "\n".join(to_str)

    def __getitem__(self, key):
        return self.tasks[key]

    def _parse_tasks(self, parsed):
        tasks = {}
        for taskname, body in parsed.items():
            logging.debug("Parsing `{}`".format(body))
            if isinstance(body, str):
                tasks[taskname] = Task(body.format(**self.vars), self.env)
            else:
                subtasks = []
                for subspec in body:
                    try:
                        subtasks.append(tasks[subspec])
                    except KeyError:
                        subtasks.append(
                            Task(subspec.format(**self.vars), self.env)
                        )
                if taskname.endswith("_c"):
                    tasks[taskname[:-2]] = ConcurrentTaskList(subtasks)
                else:
                    tasks[taskname] = SequentialTaskList(subtasks)
        return tasks


class Task(object):
    """
    An individual task with base command *cmd*.

    Arguments:

    * cmd: the base command associated with this task
    * env: a dictionary containing environment variables and their values or
           None
    """

    def __init__(self, cmd, env=None):
        logging.debug('Creating task with command "{}"'.format(cmd))
        self.cmd = cmd
        self.proc = None
        self.env = env or {}

    def terminate(self):
        """Terminate the task's process, if running"""
        try:
            if self.proc.returncode is None:
                log.debug("Terminating {}".format(self.cmd))
                self.proc.terminate()
        except AttributeError:
            pass

    async def run(self, args=None):
        """
        Run the command, with additional args if given

        Arguments:

        * args: if specified, a sequence of tokens to be appended to the base
                command
        """
        cmd = self.cmd
        if args:
            cmd = " ".join(
                [cmd, " ".join(shlex.quote(token) for token in args)]
            )
        log.info(cmd)
        self.proc = await asyncio.create_subprocess_shell(cmd, env=self.env)
        await self.proc.wait()


class TaskList(object):
    """
    Base class for Task Lists

    Arguments:

    * tasks: a sequence of :class:`Task` objecs
    """

    def __init__(self, tasks, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = tasks


class SequentialTaskList(TaskList):
    """
    A sequence of tasks of tasks to be run sequentially

    Arguments:

    * tasks: a sequence of :class:`Task` objecs
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kill = False
        self.current = None

    async def run(self, args=None):
        last = len(self.tasks) - 1
        for i, task in enumerate(self.tasks):
            if self.kill:
                break
            self.current = task
            await task.run(args if i == last else None)

    def terminate(self):
        self.kill = True
        try:
            self.current.terminate()
        except AttributeError:
            pass


class ConcurrentTaskList(TaskList):
    """
    A sequence of tasks of tasks to be run concurrently

    Arguments:

    * tasks: a sequence of :class:`Task` objecs
    """

    async def run(self, args=None):
        if args:
            error("Additional arguments not valid for concurrent tasks")
        await asyncio.wait(
            [task.run() for task in self.tasks],
            return_when=asyncio.FIRST_EXCEPTION,
        )

    def terminate(self):
        for task in self.tasks:
            task.terminate()


def parse_args():
    """ Parse cli arguments """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-f",
        "--taskfile",
        help="file containing task definitions",
        type=Path,
        default=Path("yo.yaml"),
    )
    parser.add_argument(
        "--list",
        help="list available tasks",
        action="store_true",
        default=False,
    )
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument(
        "-v",
        "--verbose",
        help="Print additional information",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    verbose.add_argument(
        "-q",
        "--quiet",
        dest="verbose",
        help="Print less information",
        action="store_const",
        const=logging.WARNING,
    )
    parser.add_argument("task", help="Name of task to execute", nargs="?")
    parser.add_argument(
        "task_args",
        help="Additional arguments to pass to task command",
        nargs=argparse.REMAINDER,
    )
    args = parser.parse_args()
    if not (args.list or args.task):
        parser.error("Must specify a task or --list")
    return args


def handle_signal(signum, task):
    """On any signal, terminate the active task"""
    log.debug("Caught {}".format(signal.Signals(signum).name))
    task.terminate()


def main():
    args = parse_args()
    logging.basicConfig(level=args.verbose)
    tasks = TaskDefs(args.taskfile)
    if args.list:
        print(tasks)
        sys.exit()
    try:
        task = tasks[args.task]
    except KeyError:
        error("Task {} not defined. {}".format(args.task, tasks))
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
        handler = functools.partial(handle_signal, sig, task)
        loop.add_signal_handler(sig, handler)
    loop.run_until_complete(task.run(args.task_args))


def dict_constructor(loader, node):
    """A constructor using OrderedDict for mappings"""
    return collections.OrderedDict(loader.construct_pairs(node))


# Add our constructor so that Tasks are in order
yaml.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dict_constructor
)


if __name__ == "__main__":
    main()
