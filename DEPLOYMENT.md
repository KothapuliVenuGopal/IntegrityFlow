# IntegrityFlow — Production Deployment Runbook

This runbook outlines the step-by-step procedures to deploy **IntegrityFlow** into a high-availability, secure production environment running **Linux (Ubuntu 22.04 / Debian 12), Nginx, Gunicorn, Python 3.11+, and MySQL 8.0+**.

---

## 1. Production Architecture Overview

```
                                  HTTPS (Port 443)
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │    Nginx    │
                                   │ Reverse     │
                                   │ Proxy & SSL │
                                   └──────┬──────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   │ Static & Media Assets                       │ Unix Socket / Proxy Pass
                   ▼                                             ▼
        ┌─────────────────────┐                       ┌─────────────────────┐
        │ /var/www/static     │                       │      Gunicorn       │
        │ /var/www/media      │                       │  WSGI Application   │
        └─────────────────────┘                       └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │   MySQL Database    │
                                                      │     (Port 3306)     │
                                                      └─────────────────────┘
```

---

## 2. Server Prerequisites & System Packages

Update system repositories and install essential packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev \
    build-essential libssl-dev libffi-dev \
    mysql-server pkg-config libmysqlclient-dev \
    nginx curl git ufw
```

---

## 3. Dedicated System User & Directory Layout

Never run the application as `root`. Create a dedicated system user:

```bash
sudo adduser --system --group --shell /bin/bash integrityflow
sudo mkdir -p /var/www/integrityflow
sudo chown -R integrityflow:integrityflow /var/www/integrityflow
```

Clone or deploy the source code into `/var/www/integrityflow`:

```bash
cd /var/www/integrityflow
git clone <repository_url> .
```

---

## 4. Production Python Virtual Environment

Create and activate an isolated virtual environment:

```bash
sudo -u integrityflow python3 -m venv /var/www/integrityflow/venv
sudo -u integrityflow /var/www/integrityflow/venv/bin/pip install --upgrade pip wheel setuptools
sudo -u integrityflow /var/www/integrityflow/venv/bin/pip install -r requirements.txt
sudo -u integrityflow /var/www/integrityflow/venv/bin/pip install gunicorn
```

---

## 5. MySQL Database Provisioning

Log into MySQL as root and provision a dedicated database and user:

```sql
-- Connect to MySQL
sudo mysql

-- Create database with UTF-8 support
CREATE DATABASE integrityflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create dedicated application user
CREATE USER 'integrityflow_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'ChangeThisToAStrongRandomPassword123!';

-- Grant required permissions
GRANT ALL PRIVILEGES ON integrityflow.* TO 'integrityflow_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 6. Environment Configuration (`.env`)

Create a secured `.env` configuration file in `/var/www/integrityflow/.env`:

```bash
sudo -u integrityflow nano /var/www/integrityflow/.env
```

Populate with production values:

```ini
# Django Core
SECRET_KEY="generate-a-secure-random-64-character-string-here"
DEBUG=False
ALLOWED_HOSTS="integrityflow.yourdomain.edu,www.integrityflow.yourdomain.edu,127.0.0.1"

# Database Configuration (MySQL)
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_NAME="integrityflow"
DB_USER="integrityflow_user"
DB_PASSWORD="ChangeThisToAStrongRandomPassword123!"

# Security and Domain
CSRF_TRUSTED_ORIGINS="https://integrityflow.yourdomain.edu"
SECURE_SSL_REDIRECT=True
```

Set strict file permissions so only the `integrityflow` user can read credentials:

```bash
sudo chmod 600 /var/www/integrityflow/.env
```

---

## 7. Database Migrations & Static Asset Collection

Execute migrations and compile static assets:

```bash
cd /var/www/integrityflow

# Apply database schema
sudo -u integrityflow /var/www/integrityflow/venv/bin/python3 manage.py migrate

# Collect static assets into STATIC_ROOT
sudo -u integrityflow /var/www/integrityflow/venv/bin/python3 manage.py collectstatic --noinput

# Create administrative superuser
sudo -u integrityflow /var/www/integrityflow/venv/bin/python3 manage.py createsuperuser
```

Ensure media storage directory exists with proper permissions:

```bash
sudo mkdir -p /var/www/integrityflow/media
sudo chown -R integrityflow:integrityflow /var/www/integrityflow/media
sudo chmod -R 750 /var/www/integrityflow/media
```

---

## 8. Gunicorn Application Service Configuration

Create a systemd service file at `/etc/systemd/system/integrityflow.service`:

```bash
sudo nano /etc/systemd/system/integrityflow.service
```

Add the following unit configuration:

```ini
[Unit]
Description=Gunicorn instance for IntegrityFlow
After=network.target mysql.service

[Service]
User=integrityflow
Group=integrityflow
WorkingDirectory=/var/www/integrityflow
EnvironmentFile=/var/www/integrityflow/.env
ExecStart=/var/www/integrityflow/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/integrityflow.sock \
          --access-logfile /var/log/integrityflow/access.log \
          --error-logfile /var/log/integrityflow/error.log \
          --timeout 120 \
          config.wsgi:application

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create logging directory:

```bash
sudo mkdir -p /var/log/integrityflow
sudo chown -R integrityflow:integrityflow /var/log/integrityflow
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable integrityflow
sudo systemctl start integrityflow
sudo systemctl status integrityflow
```

---

## 9. Nginx Reverse Proxy Configuration

Create an Nginx configuration file at `/etc/nginx/sites-available/integrityflow`:

```bash
sudo nano /etc/nginx/sites-available/integrityflow
```

Configure proxy headers and static caching:

```nginx
server {
    listen 80;
    server_name integrityflow.yourdomain.edu www.integrityflow.yourdomain.edu;

    # Maximum file upload size for evidence documents
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /var/www/integrityflow/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Media files (Chain of Custody evidence)
    location /media/ {
        alias /var/www/integrityflow/media/;
        # Restrict direct directory listings
        autoindex off;
    }

    # Proxy application requests to Gunicorn socket
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/integrityflow.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and verify syntax:

```bash
sudo ln -s /etc/nginx/sites-available/integrityflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 10. SSL/TLS Certificate with Let's Encrypt (Certbot)

Install Certbot and request automated certificates:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d integrityflow.yourdomain.edu -d www.integrityflow.yourdomain.edu
```

Certbot will automatically install SSL certificates and configure HTTPS redirects in Nginx.

---

## 11. Production Security Verification

Run Django's deployment security check:

```bash
cd /var/www/integrityflow
sudo -u integrityflow /var/www/integrityflow/venv/bin/python3 manage.py check --deploy
```

Verify that the following settings are active in `config/settings.py` for production:
- [x] `DEBUG = False`
- [x] `SECRET_KEY` loaded from environment
- [x] `ALLOWED_HOSTS` configured
- [x] `CSRF_COOKIE_SECURE = True`
- [x] `SESSION_COOKIE_SECURE = True`
- [x] `SECURE_SSL_REDIRECT = True`
- [x] `SECURE_HSTS_SECONDS = 31536000`
- [x] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- [x] `SECURE_HSTS_PRELOAD = True`

---

## 12. Backup & Disaster Recovery

### Automated Daily Database Backup
Create `/etc/cron.daily/integrityflow_db_backup`:

```bash
sudo nano /etc/cron.daily/integrityflow_db_backup
```

Add backup script:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/integrityflow"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

mysqldump --defaults-extra-file=/etc/mysql/backup.cnf integrityflow | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -delete
```

Make executable:

```bash
sudo chmod +x /etc/cron.daily/integrityflow_db_backup
```

---

## 13. Service Management Quick Reference

| Action | Command |
|---|---|
| View application logs | `sudo journalctl -u integrityflow -f` |
| View Nginx access logs | `sudo tail -f /var/log/nginx/access.log` |
| View Nginx error logs | `sudo tail -f /var/log/nginx/error.log` |
| Restart Gunicorn service | `sudo systemctl restart integrityflow` |
| Reload Nginx configuration | `sudo systemctl reload nginx` |
| Apply database updates | `sudo -u integrityflow /var/www/integrityflow/venv/bin/python3 manage.py migrate` |
