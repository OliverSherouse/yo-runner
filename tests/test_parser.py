import pytest
import yo

from pathlib import Path

HERE = Path(__file__).parent
YOFILE_DIR = HERE.joinpath("yofiles")


@pytest.fixture
def simplefile():
    yield yo.TaskDefs(YOFILE_DIR.joinpath("simple.yaml"))


def test_single(simplefile):
    assert simplefile["foo"].cmd == "python -c \"print('hello, world')\""


def test_multiple(simplefile):
    assert isinstance(simplefile["bar"], yo.SequentialTaskList)


def test_multiple_cmd(simplefile):
    assert simplefile["bar"].tasks[0].cmd == ("python -c \"print('hi')\"")
    assert simplefile["bar"].tasks[1].cmd == ("python -c \"print('there')\"")


def test_concurrent(simplefile):
    assert isinstance(simplefile["baz"], yo.ConcurrentTaskList)


def test_reference(simplefile):
    assert simplefile["baz"].tasks[-1].tasks[0].cmd == (
        "python -c \"print('hi')\""
    )


@pytest.fixture
def envfile():
    yield yo.TaskDefs(YOFILE_DIR.joinpath("with_env.yaml"))


def test_env(envfile):
    assert envfile.env["foo"] == "bar"


def test_task_after_env(envfile):
    assert envfile["print"].cmd == (
        "python -c \"import os; print(os.environ['foo'])\""
    )


@pytest.fixture
def varfile():
    yield yo.TaskDefs(YOFILE_DIR.joinpath("with_vars.yaml"))


def test_task_after_var(varfile):
    assert varfile["print"].cmd == 'python -c "print(bar)"'


@pytest.fixture
def env_then_vars():
    yield yo.TaskDefs(YOFILE_DIR.joinpath("env_then_vars.yaml"))


def test_env_then_vars_environ(env_then_vars):
    assert env_then_vars.env["greeting"] == "hello"


def test_env_then_vars_task(env_then_vars):
    assert env_then_vars["print"].cmd == (
        'python -c "import os; ' "print(os.envirion['greeting'] + ' world')\""
    )


@pytest.fixture
def vars_then_env():
    yield yo.TaskDefs(YOFILE_DIR.joinpath("vars_then_env.yaml"))


def test_vars_then_env_environ(vars_then_env):
    assert vars_then_env.env["myname"] == "world"


def test_vars_then_env_task(vars_then_env):
    assert vars_then_env["print"].cmd == (
        'python -c "import os; ' "print('hello ' + os.environ['myname'])\""
    )
