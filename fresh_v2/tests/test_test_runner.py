from unittest.mock import patch
import test_runner


@patch("test_runner.subprocess.run")
def test_run_all_tests(mock_run):
    mock_run.return_value.returncode = 0

    assert test_runner.run_tests() is True
    command = mock_run.call_args.args[0]
    assert command[-1] == "tests"


@patch("test_runner.subprocess.run")
def test_run_specific_target(mock_run):
    mock_run.return_value.returncode = 0

    assert test_runner.run_tests("tests/test_v2.py") is True
    command = mock_run.call_args.args[0]
    assert command[-1] == "tests/test_v2.py"


@patch("test_runner.subprocess.run")
def test_failed_tests(mock_run):
    mock_run.return_value.returncode = 1

    assert test_runner.run_tests() is False
