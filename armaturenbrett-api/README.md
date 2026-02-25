# Armaturenbrett API

A lightweight, Python-based FastAPI microservice that acts as the data provider layer for the frontend dashboard. The name "armaturenbrett" (German for "dashboard") is shared with the frontend to designate the visualization components of the Franz ecosystem.

## Features

- **FastAPI Framework:** Delivers high-performance REST endpoints with automatic OpenAPI documentation.
- **Direct PostgreSQL Integration:** Queries the `tickets_db` PostgreSQL instance (populated by `postgres-exportdienst`) to read the finalized, Llama-annotated tickets.
- **Aggregations on the Fly:** Executes SQL `GROUP BY` and `COUNT` queries to dynamically compute necessary KPIs for the frontend charts.
- **CORS Configured:** Fully integrated with Cross-Origin Resource Sharing settings to allow local frontend apps to fetch data seamlessly.

## Endpoints

1.  **`GET /api/health`**
    *   Returns status indicating the API is responsive.
2.  **`GET /api/tickets`**
    *   *Query Params:* `limit` (default: 50), `offset` (default: 0)
    *   Returns the most recent tickets in descending chronological order, along with a total count for pagination.
3.  **`GET /api/kpis`**
    *   Executes aggregations to return structured charts data points (`by_origin`, `by_category`, `by_priority`) and `total_tickets`.

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DB_HOST` | Hostname of the PostgreSQL server. | `postgres` |
| `DB_PORT` | Port of the PostgreSQL server. | `5432` |
| `DB_NAME` | Name of the database to query. | `tickets_db` |
| `DB_USER` | PostgreSQL user. | `postgres` |
| `DB_PASS` | PostgreSQL password. | `postgres` |

## Local Development

You can run this service standalone locally provided you have a running PostgreSQL database:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The Swagger Documentation will be available at `http://localhost:8000/docs`.
