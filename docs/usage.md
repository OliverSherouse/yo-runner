# Usage

## Basics

Yo tasks are defined in a yofile, generally called `yo.yaml`, in the directory
where the tasks will be run. The yofile should contain a yaml mapping where the
keys are the names of the tasks and the values are the tasks themselves. For
example, a `yo.yaml` with the line:

``` .yaml
greet: python -c "print('hello, world')"
```

will provide a task `yo greet` that prints out "hello, world".

You can also add additional arguments to the end of the `yo` command and they
will be passed through to the invoked task. So if your yofile contains the
line:

``` .yaml
serve: python -m http.server
```

the command `yo serve 8080 --directory foo/bar` will serve the contents of
directory foo/bar on port 8080.

Each individual task is a line of shell script, run in the system shell. This
means that yofiles may not be exactly compatible across operating systems. If
you've got complex lines of shell that need to be shared across various
systems, you may want a more sophisticated solution. If you're using Yo as a
personal convenience, go nuts.

## Task Lists

### Sequential Lists

In addition to individual tasks, a yofile can define task lists. A task list
simply runs each command one at a time, with each starting after the other
finishes. Only the last item in the list will receive any additional arguments
passed to yo on the command line. A yofile with the command:

``` .yaml
greet:
  - python -c "print('hello,')"
  - python -c "print('world')"
```

will print out "hello," on one line and "world" on the next.

Pressing Control-C will stop the sequence, so it's not a good idea to have a
process that doesn't end on its own before the last item in the sequence.

### Concurrent Lists

Yofiles can also designate lists as concurrent. Concurrent lists run all tasks
at the same time. You can designate a list as concurrent by appending `_c` to
the end of its name. A yofile with the command

``` .yaml
serve_c:
 - python -m http.server
 - python -m http.server 8001 --directory foo
```

will define a command `yo serve` that will serve the contents of the current
directory on port 8000 and the contents of the directory `foo` on port 8001 at
the same time. Control-C will end both.

## References

If you've defined a task, you can reference it in a later task list by name.
Simply use the name of the task as a command in the list. So a yofile with the
commands:

``` yaml
serve-docs: python -m http.server --directory docs/_build
docs:
  - poetry run sphinx-build docs docs/_build
  - serve-docs
```

will define two commands: `yo serve-docs`, which will serve the `docs/_build`
folder, and `yo docs`, which will build the docs before serving them.

References can be other lists. You can even reference a sequential list inside
a concurrent list, or a concurrent list inside a sequential one. Remember,
though, that a Control-C will always stop execution, so plan accordingly.
