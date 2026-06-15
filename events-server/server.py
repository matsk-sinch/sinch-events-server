import logging
import os

from flask import Flask, request

from conversation_api.controller import ConversationController
from routes.query_routes import init_query_routes, query_bp
from sinch_client_helper import get_sinch_client, load_config
from storage.event_repository import EventRepository

app = Flask(__name__)

config = load_config()
port = int(config.get("SERVER_PORT") or os.environ.get("SERVER_PORT") or 3001)
conversation_sinch_event_secret = config.get("CONVERSATION_SINCH_EVENT_SECRET", "")
sinch_client = get_sinch_client(config)
event_repository = EventRepository()

logging.basicConfig()
sinch_client.configuration.logger.setLevel(logging.INFO)

conversation_controller = ConversationController(
    sinch_client,
    conversation_sinch_event_secret,
    event_repository,
)

init_query_routes(event_repository)
app.register_blueprint(query_bp)


@app.before_request
def before_request():
    request.raw_body = request.get_data()


app.add_url_rule(
    "/ConversationEvent",
    methods=["POST"],
    view_func=conversation_controller.conversation_event,
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
