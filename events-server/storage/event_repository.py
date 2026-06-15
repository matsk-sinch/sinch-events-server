import os
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from sinch.domains.conversation.models.v1.sinch_events import ConversationSinchEventBase

from storage.message_id_extractor import extract_event_type, extract_message_id


class EventRepository:
    def __init__(self) -> None:
        uri = os.environ.get("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is required")

        self._database_name = os.environ.get("MONGODB_DATABASE", "sinch_events")
        self._collection_name = os.environ.get("MONGODB_COLLECTION", "events")
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self._collection: Collection = self._client[self._database_name][self._collection_name]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self._collection.create_index([("message_id", ASCENDING)])
        self._collection.create_index([("received_at", ASCENDING)])

    def ping(self) -> None:
        self._client.admin.command("ping")

    def save_event(self, event: ConversationSinchEventBase) -> None:
        document = {
            "received_at": datetime.now(timezone.utc),
            "service": "conversation",
            "event_type": extract_event_type(event),
            "message_id": extract_message_id(event),
            "payload": event.model_dump(mode="json"),
        }
        self._collection.insert_one(document)

    def find_by_message_id(self, message_id: str) -> list[dict]:
        cursor = self._collection.find({"message_id": message_id}).sort("received_at", ASCENDING)
        return [self._serialize_document(doc) for doc in cursor]

    def find_by_date_range(self, start: datetime, end: datetime) -> list[dict]:
        cursor = self._collection.find(
            {"received_at": {"$gte": start, "$lte": end}}
        ).sort("received_at", ASCENDING)
        return [self._serialize_document(doc) for doc in cursor]

    @staticmethod
    def _serialize_document(document: dict) -> dict:
        serialized = dict(document)
        serialized.pop("_id", None)
        received_at = serialized.get("received_at")
        if isinstance(received_at, datetime):
            serialized["received_at"] = received_at.isoformat()
        return serialized


def is_mongo_unavailable(error: Exception) -> bool:
    return isinstance(error, (PyMongoError, ValueError))
