# Deployment Guide

## Pre-Deployment Checklist

- [ ] Set `DEBUG = False`
- [ ] Configure `SECRET_KEY` with strong random value
- [ ] Set `ALLOWED_HOSTS` with production domain(s)
- [ ] Configure PostgreSQL database
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure email backend
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy
- [ ] Review security headers
- [ ] Disable unnecessary endpoints

## Environment Variables

Create `.env` for production:

```
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=your-very-secure-random-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=bodas_prod
DB_USER=bodas_user
DB_PASSWORD=your-secure-db-password
DB_HOST=your-db-host.rds.amazonaws.com
DB_PORT=5432

EMAIL_HOST=your-email-provider
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_PORT=587
EMAIL_USE_TLS=True

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Docker Deployment

### Build Production Image

```bash
docker build -t bodas:production .
```

### Push to Registry

```bash
docker tag bodas:production your-registry/bodas:production
docker push your-registry/bodas:production
```

### Deploy with Docker Compose

Production compose file:
```yaml
version: '3.9'

services:
  web:
    image: your-registry/bodas:production
    environment:
      - DJANGO_ENV=production
    ports:
      - "8000:8000"
    depends_on:
      - db
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Gunicorn Deployment

### Install Gunicorn
```bash
pip install gunicorn
```

### Run Gunicorn

```bash
gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --timeout 60 \
  --access-logfile - \
  config.wsgi:application
```

### Systemd Service

Create `/etc/systemd/system/bodas.service`:

```ini
[Unit]
Description=Bodas Django Application
After=network.target

[Service]
User=bodas
WorkingDirectory=/home/bodas/bodas
ExecStart=/home/bodas/bodas/venv/bin/gunicorn \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable bodas
sudo systemctl start bodas
```

## Nginx Configuration

### Reverse Proxy Setup

```nginx
upstream bodas {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 50M;

    location /static/ {
        alias /home/bodas/bodas/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/bodas/bodas/media/;
    }

    location / {
        proxy_pass http://bodas;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

## SSL/TLS Setup

Using Let's Encrypt with Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

Auto-renew:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Database Backup

### PostgreSQL Backup

```bash
pg_dump -U bodas_user -h localhost bodas > bodas_backup.sql
```

### Automated Backup Script

Create `/home/bodas/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/bodas/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_dump -U bodas_user -h localhost bodas | gzip > $BACKUP_DIR/bodas_$TIMESTAMP.sql.gz

find $BACKUP_DIR -type f -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /home/bodas/backup.sh
```

## Monitoring

### Health Check Endpoint

```bash
curl -I http://yourdomain.com/api/health/
```

### Logs

Application logs:
```bash
tail -f /var/log/bodas/access.log
tail -f /var/log/bodas/error.log
```

## Scaling

### Horizontal Scaling

1. Set up database replication
2. Deploy multiple Gunicorn instances
3. Use load balancer (Nginx, HAProxy)
4. Implement caching layer (Redis)

### Performance Optimization

- Enable query optimization
- Set up caching strategies
- Use CDN for static files
- Implement API rate limiting
- Monitor slow queries

## Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if Gunicorn is running: `ps aux | grep gunicorn`
- Check Gunicorn logs
- Verify Nginx configuration: `nginx -t`

**Static Files Not Loading**
- Collect static files: `python manage.py collectstatic`
- Verify Nginx alias paths
- Check file permissions

**Database Connection Error**
- Verify PostgreSQL is running
- Check connection string in `.env`
- Verify firewall rules

**Out of Memory**
- Reduce number of workers
- Increase server resources
- Implement caching

## Security Hardening

1. Keep system updated
2. Use strong passwords
3. Enable firewall
4. Configure fail2ban
5. Set up intrusion detection
6. Regular security audits
7. Monitor for vulnerabilities
8. Implement DDoS protection

## Rollback Procedure

```bash
docker-compose down
git checkout <previous-commit>
docker-compose up -d
```

## Maintenance Windows

Schedule maintenance during low-traffic hours.

### Database Maintenance

```bash
python manage.py dbshell < maintenance.sql
```

### Dependencies Update

```bash
pip install --upgrade -r requirements.txt
docker build -t bodas:production .
```
