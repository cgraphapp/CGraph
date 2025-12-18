#!/bin/bash

set -e

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: ./setup-ssl.sh yourdomain.com admin@yourdomain.com"
  exit 1
fi

echo "🔒 Setting up SSL for $DOMAIN..."

# Install Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Create SSL certificate
sudo certbot certonly \
  --standalone \
  -d $DOMAIN \
  -d www.$DOMAIN \
  --email $EMAIL \
  --agree-tos \
  --non-interactive \
  --cert-name cgraph

# Set up auto-renewal
sudo certbot renew --quiet --no-eff-email

# Create cron job for auto-renewal
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet") | crontab -

echo "✅ SSL certificate installed successfully"
echo "Certificate path: /etc/letsencrypt/live/cgraph/fullchain.pem"
echo "Key path: /etc/letsencrypt/live/cgraph/privkey.pem"

