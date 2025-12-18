"""
AWS Rekognition for content moderation
Detects inappropriate content (violence, explicit content, etc.)
"""

import boto3
import logging

logger = logging.getLogger(__name__)

class AWSRekognitionService:
    
    def __init__(self, region: str = "us-east-1"):
        self.rekognition = boto3.client('rekognition', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
    
    async def moderate_image(self, s3_bucket: str, s3_key: str) -> dict:
        """
        Moderate image using AWS Rekognition
        Returns confidence scores for unsafe content
        """
        
        try:
            response = self.rekognition.detect_moderation_labels(
                Image={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                MinConfidence=50  # 50% confidence threshold
            )
            
            moderation_labels = response.get('ModerationLabels', [])
            
            logger.info(f"Rekognition results for {s3_key}: {len(moderation_labels)} labels")
            
            return {
                'safe': len(moderation_labels) == 0,
                'labels': [
                    {
                        'name': label['Name'],
                        'confidence': label['Confidence'],
                        'parent': label.get('ParentName')
                    }
                    for label in moderation_labels
                ],
                'explicit_content': any(
                    label['Name'] in ['Explicit Nudity', 'Suggestive']
                    for label in moderation_labels
                ),
                'violent_content': any(
                    label['Name'] in ['Violence', 'Weapons']
                    for label in moderation_labels
                )
            }
        
        except Exception as e:
            logger.error(f"Rekognition error: {str(e)}")
            return {'safe': False, 'error': str(e)}
    
    async def detect_text_in_image(self, s3_bucket: str, s3_key: str) -> list:
        """
        Extract text from image using OCR
        Useful for finding text-based inappropriate content
        """
        
        response = self.rekognition.detect_text(
            Image={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            }
        )
        
        text_detections = response.get('TextDetections', [])
        
        # Filter to only full detections (ParentId = 0)
        full_text = []
        for detection in text_detections:
            if detection.get('Type') == 'LINE':
                full_text.append({
                    'text': detection['DetectedText'],
                    'confidence': detection['Confidence']
                })
        
        return full_text
    
    async def detect_labels(self, s3_bucket: str, s3_key: str) -> list:
        """
        Detect objects and concepts in image
        """
        
        response = self.rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            },
            MaxLabels=10,
            MinConfidence=50
        )
        
        return [
            {
                'name': label['Name'],
                'confidence': label['Confidence']
            }
            for label in response.get('Labels', [])
        ]
