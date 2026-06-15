from sinch.domains.conversation.models.v1.sinch_events import (
    ConversationSinchEventBase,
    MessageDeliveryReceiptEvent,
    MessageInboundEvent,
    MessageSubmitEvent,
)


def extract_message_id(event: ConversationSinchEventBase) -> str | None:
    if isinstance(event, MessageInboundEvent):
        return event.message.id
    if isinstance(event, MessageDeliveryReceiptEvent):
        return event.message_delivery_report.message_id
    if isinstance(event, MessageSubmitEvent):
        return event.message_submit_notification.message_id
    return None


def extract_event_type(event: ConversationSinchEventBase) -> str:
    if isinstance(event, MessageInboundEvent):
        return "MESSAGE_INBOUND"
    if isinstance(event, MessageDeliveryReceiptEvent):
        return "MESSAGE_DELIVERY"
    if isinstance(event, MessageSubmitEvent):
        return "MESSAGE_SUBMIT"
    return type(event).__name__
