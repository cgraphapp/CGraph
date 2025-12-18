# /backend/app/services/file_service.py
"""
File upload, storage, virus scanning, and CDN delivery
"""

import aioboto3
import magic
import aiofiles
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileService:
    
    ALLOWED_EXTENSIONS = {
        'images': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx'],
        'audio': ['mp3', 'wav', 'ogg', 'm4a'],
        'video': ['mp4', 'webm', 'mov']
    }
    
    MAX_FILE_SIZE = {
        'images': 10 * 1024 * 1024,  # 10 MB
        'documents': 50 * 1024 * 1024,  # 50 MB
        'audio': 100 * 1024 * 1024,  # 100 MB
        'video': 500 * 1024 * 1024  # 500 MB
    }
    
    async def upload_file(
        self,
        user_id: str,
        file: UploadFile,
        file_type: str  # 'images', 'documents', 'audio', 'video'
    ) -> str:
        """
        Upload file with validation, scanning, and CDN storage
        Returns: S3 URL
        """
        
        try:
            # 1. Validate file type
            if file.filename.split('.')[-1].lower() not in self.ALLOWED_EXTENSIONS[file_type]:
                raise InvalidFileTypeError(f"File type not allowed for {file_type}")
            
            # 2. Check file size
            file_content = await file.read()
            file_size = len(file_content)
            
            if file_size > self.MAX_FILE_SIZE[file_type]:
                raise FileTooLargeError(
                    f"File exceeds max size of {self.MAX_FILE_SIZE[file_type] / 1024 / 1024}MB"
                )
            
            # 3. Verify MIME type
            mime_type = magic.from_buffer(file_content, mime=True)
            await self._validate_mime_type(mime_type, file_type)
            
            # 4. Virus scan
            is_clean = await self._scan_for_viruses(file_content)
            if not is_clean:
                logger.warning(f"Virus detected in file from user {user_id}")
                raise VirusDetectedError()
            
            # 5. Calculate hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 6. Check for duplicate (avoid re-upload)
            existing = await db.execute(
                select(File).where(File.content_hash == file_hash)
            )
            if existing.scalar():
                logger.info(f"File {file_hash} already exists, returning existing URL")
                return existing.scalar().url
            
            # 7. Upload to S3
            s3_url = await self._upload_to_s3(
                user_id,
                file_hash,
                file_content,
                file_type,
                file.filename,
                mime_type
            )
            
            # 8. Store metadata
            file_record = File(
                user_id=user_id,
                filename=file.filename,
                mime_type=mime_type,
                size=file_size,
                content_hash=file_hash,
                url=s3_url,
                file_type=file_type,
                uploaded_at=datetime.utcnow()
            )
            db.add(file_record)
            await db.commit()
            
            logger.info(f"File uploaded: {file_hash} ({file_size} bytes)")
            
            return s3_url
        
        finally:
            await file.close()
    
    async def _validate_mime_type(self, mime_type: str, file_type: str):
        """Validate MIME type matches file type"""
        
        allowed_mimes = {
            'images': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'documents': ['application/pdf', 'application/msword', 'application/vnd.ms-excel'],
            'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'],
            'video': ['video/mp4', 'video/webm', 'video/quicktime']
        }
        
        if mime_type not in allowed_mimes[file_type]:
            raise InvalidFileTypeError(f"MIME type {mime_type} not allowed")
    
    async def _scan_for_viruses(self, file_content: bytes) -> bool:
        """Scan file for viruses using ClamAV"""
        
        try:
            import pyclamav
            
            clam = pyclamav.ClamAV()
            result = await clam.scan_stream(file_content)
            
            return result is None  # None = no virus
        except Exception as e:
            logger.error(f"Virus scan failed: {str(e)}")
            # Fail secure - don't upload if scan fails
            return False
    
    async def _upload_to_s3(
        self,
        user_id: str,
        file_hash: str,
        file_content: bytes,
        file_type: str,
        filename: str,
        mime_type: str
    ) -> str:
        """Upload file to S3 and return CDN URL"""
        
        # S3 path: uploads/{file_type}/{year}/{month}/{day}/{hash}
        now = datetime.utcnow()
        s3_key = f"uploads/{file_type}/{now.year}/{now.month:02d}/{now.day:02d}/{file_hash}"
        
        async with aioboto3.Session().client('s3', region_name=settings.AWS_REGION) as s3:
            await s3.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=s3_key,
                Body=file_content,
                ContentType=mime_type,
                Metadata={
                    'user-id': user_id,
                    'uploaded-by': 'cgraph',
                    'original-filename': filename
                },
                ServerSideEncryption='AES256'  # Encrypt at rest
            )
        
        # Return CDN URL (CloudFront)
        return f"https://{settings.CDN_DOMAIN}/{s3_key}"
    
    async def delete_file(self, file_id: str, user_id: str):
        """Delete file from S3 and database"""
        
        file_record = await db.get(File, file_id)
        
        if not file_record or file_record.user_id != user_id:
            raise FileNotFoundError()
        
        # Delete from S3
        async with aioboto3.Session().client('s3', region_name=settings.AWS_REGION) as s3:
            await s3.delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=file_record.s3_key
            )
        
        # Delete from database
        await db.delete(file_record)
        await db.commit()
        
        logger.info(f"File deleted: {file_id}")
