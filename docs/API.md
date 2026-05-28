# API Documentation

## Overview

The Bodas API provides comprehensive endpoints for managing wedding events, vendors, payments, and related resources.

## Authentication

All endpoints require authentication via token or session:

```bash
Authorization: Token <your-token>
```

## Endpoints

### Events

**List Events**
```
GET /api/events/
```

**Create Event**
```
POST /api/events/
Content-Type: application/json

{
  "nombre": "Wedding Event",
  "tipo_id": 1,
  "ubicacion_id": 1,
  "fecha_inicio": "2024-12-15T10:00:00Z",
  "fecha_fin": "2024-12-15T22:00:00Z",
  "max_asistentes": 200,
  "descripcion": "Annual wedding celebration",
  "presupuesto": 50000
}
```

**Get Event**
```
GET /api/events/{id}/
```

**Update Event**
```
PUT /api/events/{id}/
PATCH /api/events/{id}/
```

**Delete Event**
```
DELETE /api/events/{id}/
```

### Locations (Ubicaciones)

**List Locations**
```
GET /api/locations/
```

**Create Location**
```
POST /api/locations/
Content-Type: application/json

{
  "nombre": "Venue Name",
  "direccion": "123 Main St",
  "ciudad": "City",
  "capacidad": 500
}
```

### Providers (Proveedores)

**List Providers**
```
GET /api/providers/
```

**Get Provider**
```
GET /api/providers/{id}/
```

### Transactions (Transacciones)

**List Transactions**
```
GET /api/transactions/
```

**Get Transaction**
```
GET /api/transactions/{id}/
```

## Response Format

Success Response (200):
```json
{
  "id": 1,
  "nombre": "Event Name",
  "tipo": {
    "id": 1,
    "nombre": "Wedding"
  },
  "fecha_inicio": "2024-12-15T10:00:00Z",
  "fecha_fin": "2024-12-15T22:00:00Z",
  "creado_en": "2024-01-01T12:00:00Z"
}
```

Error Response (400):
```json
{
  "field_name": [
    "Error message"
  ]
}
```

## Pagination

List endpoints support pagination:

```
GET /api/events/?page=1&page_size=20
```

## Filtering

Filter by event type:
```
GET /api/events/?tipo=1
```

Search events:
```
GET /api/events/?search=wedding
```

## Rate Limiting

API rate limits: 1000 requests per hour per user

## Errors

| Code | Message |
|------|---------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## API Schema

Interactive schema available at `/api/schema/`
