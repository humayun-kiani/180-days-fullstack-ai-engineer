# Day 26 — Deployment: Nginx, SSL, Docker Compose Production & Cloud VPS

> **Phase 2 — Web Development** | Week 5 | Day 26 of 180

---

## 📌 What I Learned Today

- Why development and production configurations differ
- VPS (Virtual Private Server) — renting a Linux cloud server
- Initial server setup: UFW firewall, non-root user, SSH keys
- Docker installation on Ubuntu 22.04
- Multi-stage Dockerfile: dependencies stage → production stage
- Running as non-root user inside Docker container
- Gunicorn with UvicornWorker: -w 4 for multi-process production
- TrustedHostMiddleware — reject invalid Host headers
- GZipMiddleware — compress responses automatically
- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options
- Nginx as reverse proxy — why it sits in front of the app
- nginx.conf: worker_processes auto, keepalive, gzip, rate limiting
- limit_req_zone: API rate limit (30r/s) vs auth rate limit (5r/m)
- Let's Encrypt + Certbot — free automated SSL certificates
- ACME challenge over HTTP — how certificate validation works
- SSL/TLS settings: TLSv1.2/1.3, ECDHE ciphers, OCSP stapling
- SSL Labs A+ configuration
- docker-compose.prod.yml vs docker-compose.dev.yml
- expose vs ports in Docker Compose (internal vs external)
- Container restart policies: unless-stopped
- Docker logging: json-file driver with rotation
- Named volumes for persistent data
- Certbot auto-renewal loop (every 12 hours)
- deploy.sh: validated first deployment
- update.sh: zero-downtime rolling update
- backup.sh: daily PostgreSQL backup with 7-day retention
- DNS A record configuration
- Uptime monitoring with UptimeRobot
- WEB_CONCURRENCY: 2 × CPU cores for optimal workers

## 🔨 Project Built

**Production Deployment Stack** — Complete infrastructure:

- Multi-stage Dockerfile (dependencies + slim production image)
- docker-compose.prod.yml: nginx, certbot, app, db, cache,
  celery_worker, celery_beat — all 7 services
- docker-compose.dev.yml: development with hot-reload
- Nginx HTTP config with ACME challenge support
- Nginx HTTPS config with A+ SSL settings + rate limiting
- Security headers on every response
- 4 deployment scripts: deploy, update, backup, init-ssl
- .env.example and .env.production.example templates
- Production FastAPI app: TrustedHostMiddleware, GZip,
  security headers, docs disabled in prod
- Complete README with step-by-step deployment instructions

## 🚀 How to Deploy

```bash
# On your server (Ubuntu 22.04 VPS):

# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Clone your repo
git clone https://github.com/yourusername/your-repo
cd your-repo/Day-26-Deployment

# 3. Configure environment
cp .env.production.example .env
nano .env    # fill in all values!

# 4. Deploy
chmod +x scripts/*.sh
./scripts/deploy.sh

# 5. Set up SSL
./scripts/init-ssl.sh

# 6. Check it works
curl https://api.yourdomain.com/health
```

## 🧠 Production Checklist

| Item                       | Why                               |
| -------------------------- | --------------------------------- |
| Non-root user in Docker    | Security                          |
| DEBUG=false                | Performance + don't expose errors |
| Docs disabled in prod      | Don't expose API structure        |
| HTTPS only                 | Encrypt all traffic               |
| DB not exposed to internet | Only internal network             |
| Rate limiting on auth      | Prevent brute force               |
| Log rotation               | Prevent disk full                 |
| Named volumes              | Data persists across restarts     |
| Health checks              | Detect failures automatically     |
| Daily backups              | Recover from data loss            |
| Uptime monitoring          | Know when it goes down            |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
