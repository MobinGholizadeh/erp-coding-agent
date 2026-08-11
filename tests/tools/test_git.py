import pytest
import os
import subprocess
from pathlib import Path
from erp_coding_agent.tools.security import SecurityManager
from erp_coding_agent.config.settings import RepositorySettings
from erp_coding_agent.tools.git import GitStatusTool, GitDiffTool, GitCheckpointTool, GitRollbackTool

@pytest.fixture
def git_repo(tmp_path):
    # Initialize a temporary git repository
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True)
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial")
    subprocess.run(["git", "add", "test.txt"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(tmp_path), check=True)
    
    return tmp_path

@pytest.fixture
def security_manager(git_repo):
    settings = RepositorySettings(root=str(git_repo))
    return SecurityManager(settings)

@pytest.mark.asyncio
async def test_git_status(security_manager):
    tool = GitStatusTool(security_manager)
    res = await tool.execute()
    assert res.exit_code == 0
    assert "working tree clean" in res.status

@pytest.mark.asyncio
async def test_git_diff(security_manager, git_repo):
    (git_repo / "test.txt").write_text("modified")
    
    tool = GitDiffTool(security_manager)
    res = await tool.execute()
    assert res.exit_code == 0
    assert "modified" in res.diff

@pytest.mark.asyncio
async def test_git_checkpoint(security_manager, git_repo):
    (git_repo / "new.txt").write_text("new file")
    
    tool = GitCheckpointTool(security_manager)
    res = await tool.execute(message="Add new file")
    assert res.success
    
    status = subprocess.run(["git", "status"], cwd=str(git_repo), capture_output=True, text=True)
    assert "working tree clean" in status.stdout

@pytest.mark.asyncio
async def test_git_rollback(security_manager, git_repo):
    (git_repo / "test.txt").write_text("modified")
    
    tool = GitRollbackTool(security_manager)
    res = await tool.execute() # defaults to HEAD
    
    assert res.success
    assert (git_repo / "test.txt").read_text() == "initial"
