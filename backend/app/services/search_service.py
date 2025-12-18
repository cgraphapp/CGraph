# /backend/app/services/search_service.py
"""
Full-text search using Elasticsearch
"""

from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

class SearchService:
    
    def __init__(self):
        self.es = Elasticsearch([settings.ELASTICSEARCH_URL])
    
    async def index_message(self, message: Message):
        """Index message for full-text search"""
        
        try:
            await self.es.index(
                index="messages",
                id=str(message.id),
                body={
                    "message_id": str(message.id),
                    "room_id": str(message.room_id),
                    "sender_id": str(message.sender_id),
                    "content": message.content,
                    "created_at": message.created_at,
                    "timestamp": int(message.created_at.timestamp())
                }
            )
        except Exception as e:
            logger.error(f"Failed to index message: {str(e)}")
    
    async def search_messages(
        self,
        query: str,
        room_id: str = None,
        user_id: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> list:
        """Search messages"""
        
        # Build Elasticsearch query
        es_query = {
            "multi_match": {
                "query": query,
                "fields": ["content^2", "sender_id"]
            }
        }
        
        filters = []
        if room_id:
            filters.append({"term": {"room_id": room_id}})
        if user_id:
            filters.append({"term": {"sender_id": user_id}})
        
        search_body = {
            "query": {
                "bool": {
                    "must": [es_query],
                    "filter": filters if filters else None
                }
            },
            "sort": [{"created_at": "desc"}],
            "from": offset,
            "size": limit
        }
        
        # Execute search
        result = await self.es.search(index="messages", body=search_body)
        
        # Return results
        messages = []
        for hit in result['hits']['hits']:
            messages.append(hit['_source'])
        
        return messages
    
    async def delete_message(self, message_id: str):
        """Remove message from search index"""
        
        try:
            await self.es.delete(index="messages", id=message_id)
        except Exception as e:
            logger.error(f"Failed to delete message from index: {str(e)}")
