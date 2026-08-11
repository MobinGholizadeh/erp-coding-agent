import pytest
import asyncio
from pathlib import Path
from erp_coding_agent.tools.security import SecurityManager, PathBoundaryError, CommandExecutionError
from erp_coding_agent.config.settings import RepositorySettings

@pytest.fixture
def repo_root(tmp_path):
    return tmp_path

@pytest.fixture
def security_manager(repo_root):
    settings = RepositorySettings(root=str(repo_root))
    return SecurityManager(settings)

def test_validate_path_inside_repo(security_manager, repo_root):
    # Absolute inside
    path1 = repo_root / "src" / "main.py"
    res1 = security_manager.validate_path(str(path1))
    assert res1 == path1.resolve()

    # Relative inside
    res2 = security_manager.validate_path("src/main.py")
    assert res2 == (repo_root / "src" / "main.py").resolve()

def test_validate_path_outside_repo(security_manager, repo_root):
    # Absolute outside
    outside_path = repo_root.parent / "other_repo"
    with pytest.raises(PathBoundaryError):
        security_manager.validate_path(str(outside_path))

    # Path traversal outside
    with pytest.raises(PathBoundaryError):
        security_manager.validate_path("../outside.py")
        
    # Tricky path traversal
    with pytest.raises(PathBoundaryError):
        security_manager.validate_path("src/../../outside.py")

@pytest.mark.asyncio
async def test_run_controlled_command_success(security_manager, repo_root):
    # Use python -c to run a simple cross-platform command
    code, stdout, stderr = await security_manager.run_controlled_command(
        ["python", "-c", "print('hello')"],
        cwd=str(repo_root)
    )
    assert code == 0
    assert "hello" in stdout

@pytest.mark.asyncio
async def test_run_controlled_command_timeout(security_manager, repo_root):
    with pytest.raises(CommandExecutionError) as exc:
        await security_manager.run_controlled_command(
            ["python", "-c", "import time; time.sleep(2)"],
            cwd=str(repo_root),
            timeout=1
        )
    assert "timed out" in str(exc.value)

@pytest.mark.asyncio
async def test_run_controlled_command_output_limit(security_manager, repo_root):
    code, stdout, stderr = await security_manager.run_controlled_command(
        ["python", "-c", "print('A' * 200)"],
        cwd=str(repo_root),
        max_output=100
    )
    assert code == 0
    assert len(stdout) < 200
    assert "Output truncated" in stdout
