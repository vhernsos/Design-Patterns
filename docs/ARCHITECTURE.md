# Architecture Documentation

## System Overview

The Bodas platform is built on a modern, scalable architecture using Django and PostgreSQL.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Web Browser / Mobile App / Third-party API Consumers       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                  Nginx / Reverse Proxy                      │
├─────────────────────────────────────────────────────────────┤
│ SSL/TLS Termination, Load Balancing, Static File Serving   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│              Application Layer (Django + DRF)               │
├─────────────────────────────────────────────────────────────┤
│ Gunicorn WSGI Server (multiple workers)                     │
│ - REST API Endpoints                                        │
│ - Web Views                                                 │
│ - Authentication & Authorization                           │
└────────────────┬──────────────────────────┬────────────────┘
                 │                          │
    ┌────────────┴────────┐      ┌──────────┴───────────┐
    │                     │      │                      │
┌───┴──────────────────┐ │   ┌──┴───────────────────┐  │
│  Cache Layer         │ │   │  Service Layer       │  │
│  - Redis (prod)      │ │   │  - Payment Gateway   │  │
│  - Sessions          │ │   │  - Email Sender      │  │
│  - Query Cache       │ │   │  - Notifications     │  │
└──────────────────────┘ │   └─────────────────────┘  │
                         │                             │
    ┌────────────────────┴────────────────────┐        │
    │                                         │        │
┌───┴──────────────────────┐  ┌──────────────┴─────┐  │
│   Database Layer         │  │  External Services │  │
├──────────────────────────┤  ├────────────────────┤  │
│  PostgreSQL              │  │  Stripe            │  │
│  - Events                │  │  PayPal            │  │
│  - Users                 │  │  MercadoPago       │  │
│  - Transactions          │  │  AWS S3            │  │
│  - Providers             │  │  Email Service     │  │
└──────────────────────────┘  └────────────────────┘  │
                              └──────────────────────┘
```

## Component Architecture

### 1. Presentation Layer

**Web Interface**
- Django templates (HTML/CSS/JavaScript)
- Responsive design
- Real-time notifications

**API Layer**
- RESTful endpoints using Django REST Framework
- OpenAPI/Swagger documentation
- JSON responses

### 2. Application Layer

**Views & Serializers**
- `web/views.py` - Web view handlers
- `web/api/views.py` - API view handlers
- `web/api/serializers/` - Data serialization

**Business Logic**
- `web/utils/` - Utility functions
- `web/services/` - Business service layer
- `web/patterns/` - Design pattern implementations

**Authentication & Authorization**
- Token-based API authentication
- Session-based web authentication
- Permission classes for API endpoints

### 3. Data Layer

**Models**
- Core entities: Event, Location, Provider, Transaction
- Relationships and constraints defined in `web/models.py`

**Database**
- PostgreSQL for production
- SQLite3 for development
- Migrations in `web/migrations/`

### 4. External Integrations

**Payment Gateways**
- Stripe adapter
- PayPal adapter
- MercadoPago adapter

**Notification System**
- Email notifications
- Event observers
- Transaction notifications

**File Storage**
- Local storage for development
- AWS S3 for production (optional)

## Design Patterns Implementation

### Creational Patterns

**Singleton Pattern**
```
Purpose: Global configuration management
Location: web/patterns/singleton.py
Usage: ConfiguracionGlobal().get_limite_asistentes()
```

**Builder Pattern**
```
Purpose: Complex event construction
Location: web/patterns/builder.py
Classes: EventoBodaBuilder, EventoConcertBuilder, DirectorEvento
```

**Prototype Pattern**
```
Purpose: Event cloning and templates
Location: web/patterns/prototype.py
Usage: Create events from existing templates
```

### Structural Patterns

**Adapter Pattern**
```
Purpose: Multiple payment gateway integration
Location: web/patterns/adapter.py
Classes: AdaptadorStripe, AdaptadorPayPal, AdaptadorMercadoPago
```

**Decorator Pattern**
```
Purpose: Dynamic event enhancement
Location: web/patterns/decorator.py
Usage: Apply decorators to events (catering, streaming, etc.)
```

**Bridge Pattern**
```
Purpose: Report generation abstraction
Location: web/patterns/bridge.py
Usage: Generate reports in different formats
```

**Composite Pattern**
```
Purpose: Event hierarchy management
Location: web/patterns/composite.py
Usage: Sub-events within main events
```

### Behavioral Patterns

**Observer Pattern**
```
Purpose: Event notification system
Location: web/patterns/observer.py
Usage: Notify multiple observers on transactions
```

**Chain of Responsibility Pattern**
```
Purpose: Event validation pipeline
Location: web/patterns/chain_of_responsibility.py
Usage: Validate events through multiple handlers
```

**Template Method Pattern**
```
Purpose: Standardized event workflows
Location: web/patterns/template_method.py
Usage: Define common event processing steps
```

## Data Model

### Core Entities

```
Evento
├── TipoEvento (Event Type)
├── Ubicacion (Location)
├── User (Organizer)
├── Servicio[] (Services)
├── ProveedorCatering (Catering Provider)
├── ProveedorStreaming (Streaming Provider)
└── Transaccion[] (Transactions)

ProveedorServicio
├── Categoria (Category)
├── Servicio[]
└── Transaccion[]

Transaccion
├── User
├── Pasarela (Payment Gateway)
├── Evento
└── Timestamp
```

## API Architecture

### REST Conventions

- **GET** - Retrieve resources
- **POST** - Create resources
- **PUT** - Full update
- **PATCH** - Partial update
- **DELETE** - Remove resources

### Pagination

Default: 10 items per page
Customizable via `?page_size=X` parameter

### Filtering & Search

- Django Filter backend for complex filters
- Full-text search support
- Custom filters per resource

### Response Format

Consistent JSON responses:
```json
{
  "id": 1,
  "name": "Value",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

Error format:
```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

## Security Architecture

### Authentication

- **API**: Token authentication (DRF Token)
- **Web**: Session authentication (Django)
- **Options**: JWT for future mobile apps

### Authorization

- Permission classes on API endpoints
- Decorator-based permissions for web views
- Role-based access control (RBAC)

### Data Protection

- CSRF tokens on all POST/PUT/DELETE forms
- SQL injection prevention via ORM
- XSS protection in templates
- HTTPS/TLS in production

### Secrets Management

- Environment variables for sensitive data
- No hardcoded credentials
- .env files excluded from git

## Performance Architecture

### Database Optimization

- Indexed foreign keys and search fields
- Query optimization with select_related()
- Pagination for large datasets
- Database connection pooling (production)

### Caching Strategy

- **Development**: In-memory Django cache
- **Production**: Redis cache
- Cache key patterns for invalidation
- Cache timeouts per resource type

### Static File Serving

- WhiteNoise for simple deployments
- CDN integration ready
- Long-term cache headers
- Compression enabled

## Scalability Considerations

### Horizontal Scaling

1. **Stateless Application**
   - No server-side session storage
   - Use external session store (Redis)

2. **Load Balancing**
   - Nginx/HAProxy for distribution
   - Session affinity via sticky sessions (if needed)

3. **Database Scaling**
   - Read replicas for reporting
   - Write master for transactions
   - Connection pooling

4. **Cache Cluster**
   - Redis Cluster for high availability
   - Automatic failover

### Vertical Scaling

- Increase worker processes
- Increase server resources
- Optimize queries
- Improve caching

## Deployment Architecture

### Development

```
Local Machine
├── Django Dev Server (port 8000)
├── SQLite Database
└── File System Storage
```

### Production

```
Load Balancer (Nginx)
├── Gunicorn Instance 1
├── Gunicorn Instance 2
├── Gunicorn Instance 3
└── Gunicorn Instance N

PostgreSQL Master/Replica
Redis Cluster
S3/Cloud Storage
```

## CI/CD Architecture

Recommended pipeline:

1. **Test** - Run test suite
2. **Lint** - Code quality checks
3. **Build** - Docker image creation
4. **Security** - Vulnerability scanning
5. **Deploy Staging** - Pre-production testing
6. **Deploy Production** - Production release

## Monitoring & Logging

### Application Metrics

- Request count and latency
- Error rates
- Database query times
- Cache hit/miss ratios

### Business Metrics

- Event creation rate
- Transaction volume
- Revenue by payment method
- User activity

### Logs

- Application logs (Django)
- Access logs (Nginx)
- Error logs
- Audit logs (for transactions)

## Future Enhancements

1. GraphQL API alongside REST
2. WebSocket support for real-time updates
3. Microservices architecture (if needed)
4. Machine learning for recommendations
5. Mobile application (iOS/Android)
6. Advanced analytics dashboard
7. Payment webhook processing
8. Integration with external platforms
