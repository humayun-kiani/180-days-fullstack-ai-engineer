#!/bin/bash
# ============================================================
# scripts/init-ssl.sh
# Initialize SSL certificate with Let's Encrypt
#
# Run ONCE on first deployment to get SSL certificate.
# Certbot container handles renewals automatically.
# ============================================================

set -e    # exit on any error

# Load environment
source .env

DOMAIN="${DOMAIN:-api.yourdomain.com}"
EMAIL="${EMAIL:-your@email.com}"

echo "================================================="
echo "  SSL Certificate Setup for ${DOMAIN}"
echo "================================================="

# ── Step 1: Start nginx with HTTP-only config ────────────
echo ""
echo "Step 1: Starting nginx for ACME challenge..."
echo "  (Make sure app-ssl.conf is commented out or removed)"

# Temporarily use only HTTP config (for ACME challenge)
docker compose -f docker-compose.prod.yml up -d nginx certbot
sleep 5

# ── Step 2: Get certificate ──────────────────────────────
echo ""
echo "Step 2: Requesting certificate from Let's Encrypt..."
echo "  Domain: ${DOMAIN}"
echo "  Email: ${EMAIL}"

docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    -d "${DOMAIN}" \
    --staging    # Remove --staging for real certificate!

# ── Step 3: Enable HTTPS config ──────────────────────────
echo ""
echo "Step 3: Enabling HTTPS configuration..."
echo "  Uncomment the ssl server block in nginx/conf.d/app.conf"
echo "  Or rename app-ssl.conf to be included"

# ── Step 4: Reload nginx ──────────────────────────────────
echo ""
echo "Step 4: Reloading nginx with SSL config..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo ""
echo "================================================="
echo "  ✅ SSL certificate obtained!"
echo "  Certificate location: ./certbot/conf/live/${DOMAIN}/"
echo "  Renewal: automatic every 12 hours via certbot container"
echo "================================================="
echo ""
echo "  IMPORTANT: Remove --staging flag from this script"
echo "  and run again to get a REAL (not test) certificate!"