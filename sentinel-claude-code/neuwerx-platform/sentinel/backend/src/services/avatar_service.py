"""
Avatar service for handling user profile pictures
"""
import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles

from src.models.user import User
from src.utils.exceptions import ValidationError


class AvatarService:
    """Service for handling user avatar uploads and management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Avatar configuration
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.allowed_formats = {'PNG', 'JPEG', 'JPG', 'WEBP'}
        self.avatar_sizes = {
            'thumbnail': (64, 64),
            'small': (128, 128),
            'medium': (256, 256),
            'large': (512, 512)
        }
        
        # Storage configuration
        self.storage_dir = Path("storage/avatars")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Public URL base (would be configurable in production)
        self.base_url = "http://localhost:8000/api/v1/users/avatars"
    
    async def upload_avatar(
        self, 
        user_id: str, 
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Upload and process user avatar
        
        Args:
            user_id: User ID
            file: Uploaded file
            
        Returns:
            Dict with avatar information
        """
        # Validate file
        await self._validate_file(file)
        
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValidationError("User not found")
        
        # Generate file ID and paths
        file_id = str(uuid.uuid4())
        file_extension = self._get_file_extension(file.filename)
        
        # Save original file
        original_path = self.storage_dir / f"{file_id}_original{file_extension}"
        await self._save_uploaded_file(file, original_path)
        
        # Process and save different sizes
        avatar_urls = {}
        try:
            for size_name, dimensions in self.avatar_sizes.items():
                processed_path = self.storage_dir / f"{file_id}_{size_name}{file_extension}"
                await self._resize_image(original_path, processed_path, dimensions)
                avatar_urls[size_name] = f"{self.base_url}/{file_id}_{size_name}{file_extension}"
            
            # Clean up old avatar if exists
            if user.avatar_file_id:
                await self._cleanup_old_avatar(user.avatar_file_id)
            
            # Update user record
            await self.db.execute(
                update(User).where(User.id == user_id).values(
                    avatar_file_id=file_id,
                    avatar_url=avatar_urls['medium']  # Default to medium size
                )
            )
            await self.db.commit()
            
            return {
                "file_id": file_id,
                "urls": avatar_urls,
                "default_url": avatar_urls['medium'],
                "sizes": list(self.avatar_sizes.keys())
            }
            
        except Exception as e:
            # Clean up files on error
            await self._cleanup_avatar_files(file_id)
            raise ValidationError(f"Failed to process avatar: {str(e)}")
    
    async def get_avatar(self, user_id: str, size: str = 'medium') -> Optional[Dict[str, Any]]:
        """
        Get user avatar information
        
        Args:
            user_id: User ID
            size: Avatar size (thumbnail, small, medium, large)
            
        Returns:
            Avatar information or None
        """
        if size not in self.avatar_sizes:
            raise ValidationError(f"Invalid size. Must be one of: {list(self.avatar_sizes.keys())}")
        
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.avatar_file_id:
            return None
        
        # Check if file exists
        file_extension = ".png"  # Default, could be stored in DB
        file_path = self.storage_dir / f"{user.avatar_file_id}_{size}{file_extension}"
        
        if not file_path.exists():
            return None
        
        return {
            "file_id": user.avatar_file_id,
            "url": f"{self.base_url}/{user.avatar_file_id}_{size}{file_extension}",
            "size": size,
            "file_path": str(file_path)
        }
    
    async def delete_avatar(self, user_id: str) -> bool:
        """
        Delete user avatar
        
        Args:
            user_id: User ID
            
        Returns:
            True if avatar was deleted
        """
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.avatar_file_id:
            return False
        
        # Clean up files
        await self._cleanup_avatar_files(user.avatar_file_id)
        
        # Update user record
        await self.db.execute(
            update(User).where(User.id == user_id).values(
                avatar_file_id=None,
                avatar_url=None
            )
        )
        await self.db.commit()
        
        return True
    
    async def generate_avatar_urls(self, user_id: str) -> Optional[Dict[str, str]]:
        """Generate all avatar URLs for a user"""
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.avatar_file_id:
            return None
        
        file_extension = ".png"  # Default
        urls = {}
        for size_name in self.avatar_sizes:
            urls[size_name] = f"{self.base_url}/{user.avatar_file_id}_{size_name}{file_extension}"
        
        return urls
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if not file.filename:
            raise ValidationError("No filename provided")
        
        if file.size and file.size > self.max_file_size:
            raise ValidationError(f"File too large. Maximum size: {self.max_file_size // 1024 // 1024}MB")
        
        # Check file extension
        file_ext = self._get_file_extension(file.filename).upper()
        if file_ext.lstrip('.') not in self.allowed_formats:
            raise ValidationError(f"Invalid file format. Allowed: {', '.join(self.allowed_formats)}")
        
        # Read a small portion to validate it's a valid image
        content = await file.read(1024)
        await file.seek(0)  # Reset file pointer
        
        try:
            # Basic magic number checks
            if content.startswith(b'\xff\xd8\xff'):  # JPEG
                pass
            elif content.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                pass
            elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:  # WebP
                pass
            else:
                raise ValidationError("Invalid image file")
        except Exception:
            raise ValidationError("Invalid image file")
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix.lower()
    
    async def _save_uploaded_file(self, file: UploadFile, path: Path) -> None:
        """Save uploaded file to disk"""
        async with aiofiles.open(path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            await file.seek(0)  # Reset for potential reuse
    
    async def _resize_image(self, input_path: Path, output_path: Path, size: tuple) -> None:
        """Resize image to specified dimensions"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio with center crop
                img_ratio = img.width / img.height
                target_ratio = size[0] / size[1]
                
                if img_ratio > target_ratio:
                    # Image is wider, crop width
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                elif img_ratio < target_ratio:
                    # Image is taller, crop height
                    new_height = int(img.width / target_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))
                
                # Resize to target size
                img = img.resize(size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(output_path, 'PNG', optimize=True)
        except Exception as e:
            raise ValidationError(f"Failed to process image: {str(e)}")
    
    async def _cleanup_old_avatar(self, old_file_id: str) -> None:
        """Clean up old avatar files"""
        await self._cleanup_avatar_files(old_file_id)
    
    async def _cleanup_avatar_files(self, file_id: str) -> None:
        """Clean up all avatar files for a given file_id"""
        for size_name in list(self.avatar_sizes.keys()) + ['original']:
            for ext in ['.png', '.jpg', '.jpeg', '.webp']:
                file_path = self.storage_dir / f"{file_id}_{size_name}{ext}"
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass  # Ignore cleanup errors