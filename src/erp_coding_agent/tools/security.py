from pathlib import Path
import asyncio
from typing import List, Tuple
from ..config.settings import RepositorySettings

class SecurityException(Exception):
    pass

class PathBoundaryError(SecurityException):
    pass

class CommandExecutionError(SecurityException):
    pass

class SecurityManager:
    def __init__(self, repo_settings: RepositorySettings):
        self.root = Path(repo_settings.root).resolve()

    def validate_path(self, path: str) -> Path:
        """
        Validates that a given path is within the repository root.
        Resolves `..` and prevents path traversal.
        """
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = self.root / target_path
            
        resolved_path = target_path.resolve()
        
        try:
            resolved_path.relative_to(self.root)
        except ValueError:
            raise PathBoundaryError(f"Access denied: Path {path} is outside the repository boundary.")
            
        return resolved_path

    async def run_controlled_command(
        self, 
        cmd: List[str], 
        cwd: str, 
        timeout: int = 30, 
        max_output: int = 10000
    ) -> Tuple[int, str, str]:
        """
        Runs a command safely, enforcing timeouts and output size limits.
        """
        # Ensure cwd is within the repo boundary
        self.validate_path(cwd)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                
                if len(stdout) > max_output:
                    stdout = stdout[:max_output] + f"\n... [Output truncated to {max_output} characters]"
                    
                if len(stderr) > max_output:
                    stderr = stderr[:max_output] + f"\n... [Output truncated to {max_output} characters]"
                    
                return process.returncode or 0, stdout, stderr
                
            except asyncio.TimeoutError:
                try:
                    process.terminate()
                    await process.wait()
                except ProcessLookupError:
                    pass
                raise CommandExecutionError(f"Command timed out after {timeout} seconds")
                
        except Exception as e:
            if isinstance(e, CommandExecutionError):
                raise
            raise CommandExecutionError(f"Failed to execute command: {str(e)}")
