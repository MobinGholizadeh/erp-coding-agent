import os
import shutil
from typing import Type
from pydantic import BaseModel, Field

from .base import BaseTool, ToolPermission
from .security import SecurityManager

class ReadFileInput(BaseModel):
    path: str = Field(description="The path of the file to read, relative to the repository root.")

class ReadFileOutput(BaseModel):
    content: str
    size: int

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file."
    input_schema = ReadFileInput
    output_schema = ReadFileOutput
    permissions = [ToolPermission.READ_ONLY]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, path: str) -> ReadFileOutput:
        target_path = self.security.validate_path(path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
            
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return ReadFileOutput(content=content, size=len(content))


class WriteFileInput(BaseModel):
    path: str = Field(description="The path of the file to write to.")
    content: str = Field(description="The full content to write to the file.")

class WriteFileOutput(BaseModel):
    success: bool
    path: str

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Overwrite an existing file with new content."
    input_schema = WriteFileInput
    output_schema = WriteFileOutput
    permissions = [ToolPermission.MODIFY_FILES]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, path: str, content: str) -> WriteFileOutput:
        target_path = self.security.validate_path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found. Use create_file instead: {path}")
            
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return WriteFileOutput(success=True, path=str(path))


class CreateFileInput(BaseModel):
    path: str = Field(description="The path of the file to create.")
    content: str = Field(description="The initial content of the file.")

class CreateFileOutput(BaseModel):
    success: bool
    path: str

class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new file with the given content."
    input_schema = CreateFileInput
    output_schema = CreateFileOutput
    permissions = [ToolPermission.MODIFY_FILES]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, path: str, content: str) -> CreateFileOutput:
        target_path = self.security.validate_path(path)
        if target_path.exists():
            raise FileExistsError(f"File already exists: {path}")
            
        # Ensure parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return CreateFileOutput(success=True, path=str(path))


class DeleteFileInput(BaseModel):
    path: str = Field(description="The path of the file or directory to delete.")

class DeleteFileOutput(BaseModel):
    success: bool
    path: str

class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file or directory."
    input_schema = DeleteFileInput
    output_schema = DeleteFileOutput
    permissions = [ToolPermission.MODIFY_FILES]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, path: str) -> DeleteFileOutput:
        target_path = self.security.validate_path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
            
        if target_path.is_file():
            target_path.unlink()
        else:
            shutil.rmtree(target_path)
            
        return DeleteFileOutput(success=True, path=str(path))


class EditFileInput(BaseModel):
    path: str = Field(description="The path of the file to edit.")
    start_line: int = Field(description="The starting line number to replace (1-indexed).")
    end_line: int = Field(description="The ending line number to replace (1-indexed, inclusive).")
    new_content: str = Field(description="The new content to replace the specified lines with.")

class EditFileOutput(BaseModel):
    success: bool
    path: str

class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Edit a specific line range in an existing file."
    input_schema = EditFileInput
    output_schema = EditFileOutput
    permissions = [ToolPermission.MODIFY_FILES]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, path: str, start_line: int, end_line: int, new_content: str) -> EditFileOutput:
        target_path = self.security.validate_path(path)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
            
        if start_line < 1 or end_line < start_line:
            raise ValueError("Invalid line range. Lines are 1-indexed and start_line must be <= end_line.")
            
        with open(target_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        if start_line > len(lines):
            raise ValueError(f"start_line ({start_line}) is greater than the number of lines in the file ({len(lines)}).")
            
        # Lines are 0-indexed in array, start_line is 1-indexed
        start_idx = start_line - 1
        end_idx = min(end_line, len(lines))
        
        # Replace the range
        replacement = new_content.splitlines(keepends=True)
        # Add a trailing newline to the last replacement line if it doesn't have one and there are lines coming after
        if replacement and not replacement[-1].endswith(('\n', '\r\n')) and end_idx < len(lines):
            replacement[-1] += '\n'
            
        new_lines = lines[:start_idx] + replacement + lines[end_idx:]
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        return EditFileOutput(success=True, path=str(path))
