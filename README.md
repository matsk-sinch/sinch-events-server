# Sinch Conversation Events Server + MongoDB

A Flask server that receives Sinch Conversation API webhook events, stores them in MongoDB, and exposes query endpoints to retrieve events by `messageId` or date range.

Based on the [Sinch Python SDK sinch_events example](https://github.com/sinch/sinch-sdk-python/tree/main/examples/sinch_events).

```
sinch-events-server/
├── events-server/     # Flask app (webhook + query API)
├── mongodb/           # MongoDB Docker service
└── docker-compose.yml # Local development
```

| Service | Image | Port |
|---|---|---|
| events-server | `ghcr.io/matsk-sinch/sinch-events-server:latest` | 8080 (production) / 3001 (local) |
| mongodb | `ghcr.io/matsk-sinch/sinch-events-mongodb:latest` | 27017 |

## API

### Webhook (Sinch → server)

| Method | Path | Description |
|---|---|---|
| `POST` | `/ConversationEvent` | Receives Conversation API callbacks |

Configure in the Sinch dashboard or via the Conversation API: `https://<your-domain>/ConversationEvent`

See [Conversation API callbacks](https://developers.sinch.com/docs/conversation/callbacks).

### Query (client → server)

| Method | Path | Params | Description |
|---|---|---|---|
| `GET` | `/healthz` | — | Health check (includes MongoDB ping) |
| `GET` | `/events` | `messageId` | All events for a message ID |
| `GET` | `/events/range` | `from`, `to` (ISO-8601) | Events in a date range |

Optional auth: set `QUERY_API_KEY` and pass `Authorization: Bearer <key>` on GET requests.

**Example responses:**

```bash
curl "http://localhost:3001/events?messageId=01EQBC1A3BEK731GY4YXEN0C2R"

curl "http://localhost:3001/events/range?from=2026-06-01T00:00:00Z&to=2026-06-15T23:59:59Z"
```

```json
{
  "count": 2,
  "events": [
    {
      "received_at": "2026-06-15T10:00:00+00:00",
      "service": "conversation",
      "event_type": "MESSAGE_SUBMIT",
      "message_id": "01EQBC1A3BEK731GY4YXEN0C2R",
      "payload": { }
    }
  ]
}
```

## Local development

### Option A — Docker Compose

```bash
cp events-server/.env.example events-server/.env
cp mongodb/.env.example mongodb/.env
docker compose up --build
```

Server runs at `http://localhost:3001`.

### Option B — Run server directly

1. Start MongoDB:

```bash
docker run --env-file mongodb/.env.example -p 27017:27017 sinch-events-mongodb
```

2. Install and run the server:

```bash
cd events-server
poetry install
cp .env.example .env
poetry run python server.py
```

## Environment variables

### events-server

| Variable | Required | Description |
|---|---|---|
| `SERVER_PORT` | No | Port (default `3001` local, `8080` in Docker) |
| `CONVERSATION_SINCH_EVENT_SECRET` | Yes | Sinch Event secret for signature validation |
| `ENSURE_VALID_SIGNATURE` | No | Set `true` to enforce callback signatures in production |
| `MONGODB_URI` | Yes | MongoDB connection string |
| `MONGODB_DATABASE` | No | Database name (default `sinch_events`) |
| `MONGODB_COLLECTION` | No | Collection name (default `events`) |
| `QUERY_API_KEY` | No | Bearer token for GET endpoints |

### mongodb

| Variable | Required | Description |
|---|---|---|
| `MONGO_INITDB_ROOT_USERNAME` | Yes | Root username |
| `MONGO_INITDB_ROOT_PASSWORD` | Yes | Root password |
| `MONGO_INITDB_DATABASE` | No | Initial database name |

## Deploy to Sliplane

Deploy **two services** in the same Sliplane project. Deploy MongoDB first.

### 1. MongoDB service

- Image: `ghcr.io/matsk-sinch/sinch-events-mongodb:latest`
- Env: `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`
- **Persistent volume** at `/data/db` (required)
- Note the internal hostname assigned by Sliplane

### 2. Events server service

- Image: `ghcr.io/matsk-sinch/sinch-events-server:latest`
- Env:
  - `MONGODB_URI=mongodb://<user>:<pass>@<mongodb-internal-host>:27017/sinch_events?authSource=admin`
  - `CONVERSATION_SINCH_EVENT_SECRET`
  - `SERVER_PORT=8080`
  - `ENSURE_VALID_SIGNATURE=true` (recommended)
  - `QUERY_API_KEY` (recommended)
- Health check: `GET /healthz`
- Configure Sinch webhook: `https://<events-server-domain>/ConversationEvent`

### GHCR access

Images are published on push to `main`. If packages are private, make them public under the `matsk-sinch` GitHub org or configure Sliplane with a GHCR pull secret.

## Docker (manual)

```bash
docker build -t sinch-events-server ./events-server
docker build -t sinch-events-mongodb ./mongodb

docker run --env-file mongodb/.env.example -v mongodb_data:/data/db -p 27017:27017 sinch-events-mongodb

docker run --env-file events-server/.env.example -e MONGODB_URI="mongodb://admin:change-me@host.docker.internal:27017/sinch_events?authSource=admin" -p 8080:8080 sinch-events-server
```
