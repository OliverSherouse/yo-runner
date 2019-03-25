import subprocess
import time
import urllib.request
import urllib.error

import pytest

from pathlib import Path

yofile_dir = Path(__file__).parent.joinpath("yofiles")


def check_server(server):
    try:
        urllib.request.urlopen(server)
        return True
    except urllib.error.URLError:
        return False


def test_simple():
    result = subprocess.check_output(
        ["yo", "-f", yofile_dir.joinpath("simple.yaml"), "foo"]
    ).decode()
    assert result == "hello, world\n"


def test_multiple():
    result = subprocess.check_output(
        ["yo", "-f", yofile_dir.joinpath("simple.yaml"), "bar"]
    ).decode()
    assert result == "hi\nthere\n"


def test_concurrent():
    task = subprocess.Popen(
        ["yo", "-f", yofile_dir.joinpath("simple.yaml"), "baz"]
    )
    time.sleep(2)
    try:
        assert check_server("http://localhost:8555")
        assert check_server("http://localhost:8556")
    finally:
        task.terminate()
