# Development Guide

## Project Setup

### 1. Environment Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Configuration

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata web/fixtures/providers.json
```

### 3. Run Development Server

```bash
python manage.py runserver
```

Access at `http://localhost:8000`

## Project Structure

### Core Configuration
- `config/settings/` - Environment-specific Django settings
- `config/wsgi.py` - WSGI application entry point
- `config/urls.py` - Root URL configuration

### Web Application
- `web/models.py` - Data models
- `web/views.py` - Web view functions
- `web/api/` - REST API views and serializers
- `web/patterns/` - Design pattern implementations
- `web/templates/` - HTML templates
- `web/static/` - CSS, JavaScript, images
- `web/utils/` - Utility functions and decorators

### Data & Migrations
- `web/migrations/` - Database migrations
- `web/fixtures/` - Initial data fixtures

## Code Organization

### Adding a New Model

1. Create model in `web/models.py`
2. Create serializer in `web/api/serializers/`
3. Create API view in `web/api/views.py`
4. Register in `web/admin.py`
5. Create and run migration:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Adding a New API Endpoint

1. Create serializer in `web/api/serializers/`
2. Create view in `web/api/views.py`
3. Register in `web/api/urls.py`

### Adding a New Web View

1. Create function in `web/views/`
2. Create template in `web/templates/web/`
3. Register in `web/urls.py`

## Design Patterns Used

### Singleton Pattern
**Purpose**: Ensure single instance of global configuration

**Implementation**: `web/patterns/singleton.py`

**Usage**:
```python
from web.patterns.singleton import ConfiguracionGlobal
config = ConfiguracionGlobal()
```

### Builder Pattern
**Purpose**: Construct complex events step by step

**Implementation**: `web/patterns/builder.py`

**Usage**:
```python
builder = EventoBodaBuilder()
director = DirectorEvento(builder)
event = director.construct_event(data)
```

### Adapter Pattern
**Purpose**: Integrate multiple payment gateways

**Implementation**: `web/patterns/adapter.py`

**Usage**:
```python
adapter = AdaptadorStripe()
payment = adapter.process_payment(amount, token)
```

### Observer Pattern
**Purpose**: Notify multiple observers of events

**Implementation**: `web/patterns/observer.py`

### Decorator Pattern
**Purpose**: Enhance event objects dynamically

**Implementation**: `web/patterns/decorator.py`

### Template Method Pattern
**Purpose**: Define standardized workflows

**Implementation**: `web/patterns/template_method.py`

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific Test Suite
```bash
python manage.py test web.tests.EventTests
```

### Run with Coverage
```bash
pytest --cov=web
```

### Write New Tests

Create test in `web/tests/`:
```python
from django.test import TestCase
from web.models import Evento

class EventoTests(TestCase):
    def setUp(self):
        self.evento = Evento.objects.create(...)
    
    def test_evento_creation(self):
        self.assertIsNotNone(self.evento.id)
```

## Database Migrations

### Create Migration
```bash
python manage.py makemigrations
```

### Apply Migration
```bash
python manage.py migrate
```

### Revert Migration
```bash
python manage.py migrate web 0001
```

### Squash Migrations
```bash
python manage.py squashmigrations web 0001 0010
```

## Performance Optimization

### Query Optimization
- Use `select_related()` for foreign keys
- Use `prefetch_related()` for reverse relations
- Use `.only()` to fetch specific fields

Example:
```python
events = Evento.objects.select_related('tipo', 'ubicacion')
```

### Caching
- Redis integration for production
- Default cache for development

## Security

### Important Security Practices

1. Never commit secrets to git
2. Use environment variables for sensitive data
3. Keep dependencies updated: `pip install --upgrade -r requirements.txt`
4. Always validate user input
5. Use Django ORM to prevent SQL injection
6. CSRF tokens enabled by default

## Debugging

### Enable Django Debug Toolbar

```python
# In development settings
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Print Debugging
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message: %s", value)
```

### Django Shell
```bash
python manage.py shell
```

## Common Issues

### Database Not Updating
```bash
python manage.py migrate --fake-initial
```

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

### Import Errors
Ensure virtual environment is activated:
```bash
source venv/bin/activate
```

## Making Changes

### Before Making Changes
1. Create feature branch: `git checkout -b feature/name`
2. Update requirements if adding dependencies

### After Making Changes
1. Run tests: `python manage.py test`
2. Format code: `black web config`
3. Lint code: `flake8 web config`
4. Create commit: `git commit -m "Description"`
5. Create pull request

## Code Style

Project follows PEP 8 with 100-character line limit.

### Format Code
```bash
black web config
```

### Check Linting
```bash
flake8 web config --max-line-length=100
```

## Useful Commands

```bash
python manage.py shell_plus          # Enhanced shell with imports
python manage.py dbshell             # Database shell
python manage.py dumpdata > data.json # Backup data
python manage.py loaddata data.json  # Restore data
python manage.py check               # System check
python manage.py makemigrations --dry-run  # Preview migrations
```
