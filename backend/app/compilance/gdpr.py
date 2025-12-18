# /backend/app/compliance/gdpr.py
"""
GDPR compliance features
"""

class GDPRService:
    
    async def export_user_data(self, user_id: str) -> bytes:
        """
        Export all user data (GDPR right to data portability)
        Returns ZIP file with all personal data
        """
        
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # User profile
            user = await db.get(User, user_id)
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'display_name': user.display_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
            zip_file.writestr('profile.json', json.dumps(user_data, indent=2))
            
            # Messages
            messages = await db.execute(
                select(Message).where(Message.sender_id == user_id)
            )
            messages_data = []
            for msg in messages.scalars():
                messages_data.append({
                    'id': str(msg.id),
                    'room_id': str(msg.room_id),
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat()
                })
            zip_file.writestr('messages.json', json.dumps(messages_data, indent=2))
            
            # Groups
            groups = await db.execute(
                select(Group).join(
                    GroupMember
                ).where(GroupMember.user_id == user_id)
            )
            groups_data = []
            for group in groups.scalars():
                groups_data.append({
                    'id': str(group.id),
                    'name': group.name,
                    'joined_at': group.created_at.isoformat()
                })
            zip_file.writestr('groups.json', json.dumps(groups_data, indent=2))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    async def delete_user_data(self, user_id: str):
        """
        Delete all user data (GDPR right to erasure)
        """
        
        # Delete messages
        await db.execute(delete(Message).where(Message.sender_id == user_id))
        
        # Delete from groups
        await db.execute(delete(GroupMember).where(GroupMember.user_id == user_id))
        
        # Delete user account
        user = await db.get(User, user_id)
        user.is_active = False
        user.email = f"deleted_{user_id}@cgraph.local"
        user.password_hash = None
        user.deleted_at = datetime.utcnow()
        await db.commit()
        
        # Log deletion request
        logger.info(f"User data deleted: {user_id}")
