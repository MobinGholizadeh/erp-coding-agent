import pytest
import os
from pathlib import Path
from erp_coding_agent.tools.security import SecurityManager, PathBoundaryError
from erp_coding_agent.config.settings import RepositorySettings
from erp_coding_agent.tools.filesystem import ReadFileTool, WriteFileTool, CreateFileTool, DeleteFileTool, EditFileTool

@pytest.fixture
def security_manager(tmp_path):
    settings = RepositorySettings(root=str(tmp_path))
    return SecurityManager(settings)

@pytest.mark.asyncio
async def test_read_file(security_manager, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    
    tool = ReadFileTool(security_manager)
    res = await tool.execute("test.txt")
    
    assert res.content == "hello world"
    assert res.size == 11

@pytest.mark.asyncio
async def test_write_file(security_manager, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("old")
    
    tool = WriteFileTool(security_manager)
    res = await tool.execute("test.txt", "new")
    
    assert res.success
    assert test_file.read_text() == "new"

@pytest.mark.asyncio
async def test_create_file(security_manager, tmp_path):
    tool = CreateFileTool(security_manager)
    res = await tool.execute("new_dir/new_file.txt", "content")
    
    assert res.success
    assert (tmp_path / "new_dir" / "new_file.txt").read_text() == "content"

@pytest.mark.asyncio
async def test_delete_file(security_manager, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    
    tool = DeleteFileTool(security_manager)
    res = await tool.execute("test.txt")
    
    assert res.success
    assert not test_file.exists()

@pytest.mark.asyncio
async def test_edit_file(security_manager, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("line 1\nline 2\nline 3\n")
    
    tool = EditFileTool(security_manager)
    res = await tool.execute("test.txt", 2, 2, "new line 2\n")
    
    assert res.success
    assert test_file.read_text() == "line 1\nnew line 2\nline 3\n"
