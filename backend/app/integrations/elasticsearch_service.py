"""
Elasticsearch integration for full-text search
"""

from elasticsearch import Elasticsearch
import logging

logger = logging.getLogger(__name__)

class ElasticsearchService:
    
    def __init__(self, host: str = "localhost", port: int = 9200):
        self.es = Elasticsearch([f"http://{host}:{port}"])
        self.setup_indices()
    
    def setup_indices(self):
        """Create indices if they don't exist"""
        
        # Messages index
        if not self.es.indices.exists(index="messages"):
            self.es.indices.create(index="messages", body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard",
                                "stopwords": "_english_"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "message_id": {"type": "keyword"},
                        "room_id": {"type": "keyword"},
                        "sender_id": {"type": "keyword"},
                        "content": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "created_at": {"type": "date"},
                        "timestamp": {"type": "long"}
                    }
                }
            })
    
    async def index_message(self, message_id: str, room_id: str, 
                           sender_id: str, content: str, created_at: str):
        """Index a message for search"""
        
        doc = {
            "message_id": message_id,
            "room_id": room_id,
            "sender_id": sender_id,
            "content": content,
            "created_at": created_at,
            "timestamp": int(datetime.fromisoformat(created_at).timestamp())
        }
        
        self.es.index(index="messages", id=message_id, body=doc)
        logger.info(f"Indexed message {message_id}")
    
    async def search_messages(self, query: str, room_id: str = None, 
                             limit: int = 20) -> list:
        """Search messages"""
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["content^2", "sender_id"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "size": limit,
            "sort": [{"created_at": {"order": "desc"}}]
        }
        
        if room_id:
            search_body["query"]["bool"]["filter"] = {
                "term": {"room_id": room_id}
            }
        
        results = self.es.search(index="messages", body=search_body)
        
        messages = []
        for hit in results["hits"]["hits"]:
            messages.append(hit["_source"])
        
        return messages
    
    async def delete_message(self, message_id: str):
        """Remove message from search index"""
        self.es.delete(index="messages", id=message_id)