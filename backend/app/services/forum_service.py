# /backend/app/services/forum_service.py
"""
Forum business logic: create, edit, moderate posts/threads
"""

class ForumService:
    
    async def create_forum(
        self,
        db: AsyncSession,
        name: str,
        description: str,
        category: str,
        is_public: bool = True
    ) -> Forum:
        """Create new forum"""
        
        forum = Forum(
            name=name,
            description=description,
            category=category,
            slug=name.lower().replace(" ", "-"),
            is_public=is_public
        )
        
        db.add(forum)
        await db.commit()
        await db.refresh(forum)
        
        return forum
    
    async def create_thread(
        self,
        db: AsyncSession,
        forum_id: str,
        author_id: str,
        title: str,
        content: str,
        tags: list = None
    ) -> ForumThread:
        """Create new thread"""
        
        # Verify forum exists
        forum = await db.get(Forum, forum_id)
        if not forum:
            raise NotFoundError("Forum")
        
        # Create thread
        thread = ForumThread(
            forum_id=forum_id,
            author_id=author_id,
            title=title,
            slug=title.lower().replace(" ", "-"),
            content=content,
            tags=tags or [],
            reply_count=0
        )
        
        db.add(thread)
        
        # Create original post
        post = ForumPost(
            thread_id=thread.id,
            author_id=author_id,
            content=content,
            position=1,
            is_original_post=True
        )
        db.add(post)
        
        # Update forum stats
        forum.total_posts += 1
        
        await db.commit()
        await db.refresh(thread)
        
        return thread
    
    async def reply_to_thread(
        self,
        db: AsyncSession,
        thread_id: str,
        author_id: str,
        content: str
    ) -> ForumPost:
        """Post reply to thread"""
        
        # Verify thread exists
        thread = await db.get(ForumThread, thread_id)
        if not thread:
            raise NotFoundError("Thread")
        
        if thread.is_locked:
            raise ForbiddenError(ErrorCode.FORBIDDEN, "Thread is locked")
        
        # Get next position
        next_position = thread.reply_count + 2
        
        # Create post
        post = ForumPost(
            thread_id=thread_id,
            author_id=author_id,
            content=content,
            position=next_position,
            is_original_post=False
        )
        
        db.add(post)
        
        # Update thread stats
        thread.reply_count += 1
        thread.updated_at = datetime.utcnow()
        
        # Update forum stats
        forum = await db.get(Forum, thread.forum_id)
        forum.total_posts += 1
        
        await db.commit()
        await db.refresh(post)
        
        return post
    
    async def get_thread_with_posts(
        self,
        db: AsyncSession,
        thread_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get thread with paginated posts"""
        
        thread = await db.get(ForumThread, thread_id)
        if not thread:
            raise NotFoundError("Thread")
        
        # Increment view count
        thread.view_count += 1
        await db.commit()
        
        # Get posts
        offset = (page - 1) * per_page
        result = await db.execute(
            select(ForumPost)
            .where(ForumPost.thread_id == thread_id)
            .order_by(ForumPost.position)
            .offset(offset)
            .limit(per_page)
        )
        
        posts = result.scalars().all()
        
        return {
            "thread": thread,
            "posts": posts,
            "page": page,
            "per_page": per_page,
            "total_posts": thread.reply_count + 1
        }
    
    async def moderate_thread(
        self,
        db: AsyncSession,
        thread_id: str,
        moderator_id: str,
        action: str,
        reason: str = None
    ) -> Dict:
        """
        Moderate thread (approve, reject, delete, lock, etc.)
        """
        
        thread = await db.get(ForumThread, thread_id)
        if not thread:
            raise NotFoundError("Thread")
        
        # Log moderation action
        mod_action = ForumModeration(
            forum_id=thread.forum_id,
            thread_id=thread_id,
            action=action,
            reason=reason,
            moderator_id=moderator_id
        )
        db.add(mod_action)
        
        # Apply action
        if action == "approve":
            thread.approved = True
        elif action == "reject":
            thread.approved = False
            thread.status = "rejected"
        elif action == "delete":
            thread.status = "deleted"
        elif action == "lock":
            thread.is_locked = True
        elif action == "pin":
            thread.is_pinned = True
        elif action == "unpin":
            thread.is_pinned = False
        
        await db.commit()
        
        return {
            "message": f"Thread {action}ed successfully",
            "thread_id": thread_id
        }
    
    async def ban_user(
        self,
        db: AsyncSession,
        forum_id: str,
        user_id: str,
        moderator_id: str,
        reason: str,
        duration_days: int = None
    ) -> Dict:
        """
        Ban user from forum
        """
        
        forum = await db.get(Forum, forum_id)
        if not forum:
            raise NotFoundError("Forum")
        
        # Add to banned list
        if user_id not in forum.banned_users:
            forum.banned_users.append(user_id)
        
        # Log action
        mod_action = ForumModeration(
            forum_id=forum_id,
            user_id=user_id,
            action="ban",
            reason=reason,
            moderator_id=moderator_id,
            duration_days=duration_days
        )
        
        if duration_days:
            mod_action.expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        db.add(mod_action)
        await db.commit()
        
        return {
            "message": f"User banned from forum",
            "user_id": user_id,
            "duration_days": duration_days
        }

# API Endpoints
@router.post("/forums")
async def create_forum(
    name: str,
    description: str,
    category: str,
    db: AsyncSession = Depends(get_db),
    current_admin: str = Depends(get_admin_user)
):
    """Create new forum"""
    forum = await ForumService.create_forum(db, name, description, category)
    return forum

@router.post("/forums/{forum_id}/threads")
async def create_thread(
    forum_id: str,
    title: str,
    content: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create thread in forum"""
    thread = await ForumService.create_thread(db, forum_id, current_user, title, content)
    return thread

@router.post("/threads/{thread_id}/reply")
async def reply_to_thread(
    thread_id: str,
    content: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Reply to thread"""
    post = await ForumService.reply_to_thread(db, thread_id, current_user, content)
    return post

@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Get thread with posts"""
    return await ForumService.get_thread_with_posts(db, thread_id, page)

@router.post("/threads/{thread_id}/moderate")
async def moderate_thread(
    thread_id: str,
    action: str,
    reason: str = None,
    db: AsyncSession = Depends(get_db),
    current_moderator: str = Depends(get_moderator_user)
):
    """Moderate thread"""
    return await ForumService.moderate_thread(db, thread_id, current_moderator, action, reason)
