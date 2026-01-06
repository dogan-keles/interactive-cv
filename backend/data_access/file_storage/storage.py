"""
File storage abstraction for CV files and other documents.

Provides an interface for storing and retrieving files.
Concrete implementations can use local filesystem, S3, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorage(ABC):
    """Abstract interface for file storage operations."""
    
    @abstractmethod
    async def save_file(
        self,
        content: bytes,
        file_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Save file content to storage.
        
        Args:
            content: File content as bytes
            file_path: Relative path for the file
            content_type: Optional MIME type
            
        Returns:
            URL or path to access the file
        """
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        file_path: str,
    ) -> Optional[str]:
        """
        Get URL or path to access a file.
        
        Args:
            file_path: Relative path of the file
            
        Returns:
            URL or path, or None if file doesn't exist
        """
        pass
    
    @abstractmethod
    async def file_exists(
        self,
        file_path: str,
    ) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Relative path of the file
            
        Returns:
            True if file exists, False otherwise
        """
        pass


class LocalFileStorage(FileStorage):
    """
    Local filesystem storage implementation.
    
    Stores files in a local directory.
    """
    
    def __init__(
        self,
        base_directory: str = "storage",
        base_url: str = "/files",
    ):
        """
        Initialize local file storage.
        
        Args:
            base_directory: Base directory for file storage
            base_url: Base URL prefix for file access
        """
        self.base_directory = Path(base_directory)
        self.base_url = base_url
        self.base_directory.mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self,
        content: bytes,
        file_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Save file to local filesystem."""
        full_path = self.base_directory / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file: {full_path}")
        return f"{self.base_url}/{file_path}"
    
    async def get_file_url(
        self,
        file_path: str,
    ) -> Optional[str]:
        """Get URL for local file."""
        full_path = self.base_directory / file_path
        
        if not full_path.exists():
            return None
        
        return f"{self.base_url}/{file_path}"
    
    async def file_exists(
        self,
        file_path: str,
    ) -> bool:
        """Check if file exists in local filesystem."""
        full_path = self.base_directory / file_path
        return full_path.exists()

