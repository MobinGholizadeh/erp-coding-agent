import pytest
import sys
from pathlib import Path
from erp_coding_agent.execution.process_runner import ProcessRunner, ProcessExecutionError
from erp_coding_agent.execution.build_runner import BuildRunner
from erp_coding_agent.execution.test_runner import TestRunner
from erp_coding_agent.execution.parsers.generic import GenericBuildParser, GenericTestParser

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def process_runner(temp_dir):
    return ProcessRunner(cwd=str(temp_dir), timeout_seconds=2)

@pytest.mark.asyncio
async def test_process_runner_success(process_runner):
    res = await process_runner.run([sys.executable, "-c", "print('hello')"])
    assert res.success
    assert res.exit_code == 0
    assert "hello" in res.stdout

@pytest.mark.asyncio
async def test_process_runner_timeout(process_runner):
    # This will sleep for 5 seconds, but timeout is 2
    res = await process_runner.run([sys.executable, "-c", "import time; time.sleep(5)"])
    assert not res.success
    assert res.exit_code == -1
    assert "timed out" in res.stderr

@pytest.mark.asyncio
async def test_build_runner_with_error(temp_dir, process_runner):
    script_path = temp_dir / "mock_build.py"
    script_path.write_text("print('error: syntax error in main.py')\nimport sys; sys.exit(1)")
    
    command = f'"{Path(sys.executable).as_posix()}" "{script_path.as_posix()}"'
    parser = GenericBuildParser()
    runner = BuildRunner(command, parser, process_runner)
    
    res = await runner.run()
    assert not res.success
    assert res.exit_code == 1
    assert len(res.errors) == 1
    assert res.errors[0].message == "syntax error in main.py"

@pytest.mark.asyncio
async def test_test_runner_with_failure(temp_dir, process_runner):
    script_path = temp_dir / "mock_test.py"
    script_path.write_text("print('failed: test_something')\nimport sys; sys.exit(1)")
    
    command = f'"{Path(sys.executable).as_posix()}" "{script_path.as_posix()}"'
    parser = GenericTestParser()
    runner = TestRunner(command, parser, process_runner)
    
    res = await runner.run()
    assert not res.success
    assert res.exit_code == 1
    assert res.failed == 1
    assert len(res.failures) == 1
    assert res.failures[0].message == "test_something"
