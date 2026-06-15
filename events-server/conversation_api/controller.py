import os

from flask import Response, request

from conversation_api.server_business_logic import handle_conversation_event
from storage.event_repository import EventRepository


class ConversationController:
    def __init__(self, sinch_client, sinch_event_secret, event_repository: EventRepository):
        self.sinch_client = sinch_client
        self.sinch_event_secret = sinch_event_secret
        self.event_repository = event_repository
        self.logger = self.sinch_client.configuration.logger
        self.ensure_valid_signature = os.environ.get("ENSURE_VALID_SIGNATURE", "").lower() in {
            "1",
            "true",
            "yes",
        }

    def conversation_event(self):
        headers = dict(request.headers)
        raw_body = request.raw_body if request.raw_body else b""

        sinch_events_service = self.sinch_client.conversation.sinch_events(
            self.sinch_event_secret
        )

        if self.ensure_valid_signature:
            valid = sinch_events_service.validate_authentication_header(
                headers=headers,
                json_payload=raw_body,
            )
            if not valid:
                return Response(status=401)

        event = sinch_events_service.parse_event(raw_body, headers)
        handle_conversation_event(
            event=event,
            logger=self.logger,
            event_repository=self.event_repository,
        )

        return Response(status=200)
