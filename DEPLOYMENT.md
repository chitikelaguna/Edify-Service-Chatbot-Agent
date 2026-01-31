# 🚀 Deployment Guide - Step by Step

This guide will walk you through deploying the Edify Chatbot Agent with a custom domain, SSL certificate, and production-ready configuration.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Option A: Deploy on VPS/Server (Recommended)](#option-a-deploy-on-vpsserver-recommended)
3. [Option B: Deploy on Cloud Platform](#option-b-deploy-on-cloud-platform)
4. [Domain Configuration](#domain-configuration)
5. [SSL/TLS Setup with Let's Encrypt](#ssltls-setup-with-lets-encrypt)
6. [Reverse Proxy Setup (Nginx)](#reverse-proxy-setup-nginx)
7. [Production Docker Compose](#production-docker-compose)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- ✅ A server/VPS (Ubuntu 20.04+ recommended) or cloud account
- ✅ A domain name (e.g., `chatbot.yourdomain.com`)
- ✅ SSH access to your server
- ✅ Docker and Docker Compose installed
- ✅ Port 80 and 443 open in firewall
- ✅ All environment variables ready (`.env` file)

---

## Option A: Deploy on VPS/Server (Recommended)

### Step 1: Prepare Your Server

#### 1.1 Connect to Your Server

```bash
ssh root@your-server-ip
# or
ssh username@your-server-ip
```

#### 1.2 Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.3 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 1.4 Configure Firewall

```bash
# Install UFW (if not installed)
sudo apt install ufw -y

# Allow SSH, HTTP, and HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Step 2: Upload Your Application

#### 2.1 Create Application Directory

```bash
sudo mkdir -p /opt/edify-chatbot
cd /opt/edify-chatbot
```

#### 2.2 Upload Files to Server

**Option 1: Using Git (Recommended)**

```bash
# On your local machine, ensure code is in a Git repository
# Then on server:
sudo git clone https://your-repo-url.git /opt/edify-chatbot
cd /opt/edify-chatbot
```

**Option 2: Using SCP**

```bash
# On your local machine:
scp -r . username@your-server-ip:/opt/edify-chatbot/
```

**Option 3: Using rsync**

```bash
# On your local machine:
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
  ./ username@your-server-ip:/opt/edify-chatbot/
```

### Step 3: Configure Environment Variables

#### 3.1 Create `.env` File

```bash
cd /opt/edify-chatbot
sudo nano .env
```

Add all required environment variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Edify Supabase (READ-ONLY)
EDIFY_SUPABASE_URL=https://your-edify-project.supabase.co
EDIFY_SUPABASE_SERVICE_ROLE_KEY=your_edify_service_role_key

# Chatbot Supabase (READ/WRITE)
CHATBOT_SUPABASE_URL=https://your-chatbot-project.supabase.co
CHATBOT_SUPABASE_SERVICE_ROLE_KEY=your_chatbot_service_role_key

# Environment Configuration
ENV=production
LOG_LEVEL=INFO

# Port Configuration (default 8080)
PORT=8080

# CORS Configuration (update with your domain)
CORS_ALLOW_ORIGINS=https://chatbot.yourdomain.com,https://www.yourdomain.com

# Optional: Enable optimizations
ENABLE_COMPRESSION=true
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=300
```

#### 3.2 Secure the `.env` File

```bash
sudo chmod 600 .env
sudo chown $USER:$USER .env
```

### Step 4: Build and Test Docker Container

#### 4.1 Build the Image

```bash
cd /opt/edify-chatbot
docker build -t edify-chatbot:latest .
```

#### 4.2 Test Run (Optional)

```bash
# Run container to test
docker run -d \
  --name edify-chatbot-test \
  -p 8080:8080 \
  --env-file .env \
  edify-chatbot:latest

# Check logs
docker logs edify-chatbot-test

# Test health endpoint
curl http://localhost:8080/health

# Stop test container
docker stop edify-chatbot-test
docker rm edify-chatbot-test
```

---

## Domain Configuration

### Step 5: Configure DNS

#### 5.1 Add DNS A Record

Go to your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare) and add:

**Type:** A Record  
**Name:** `chatbot` (or `@` for root domain)  
**Value:** Your server's IP address  
**TTL:** 3600 (or default)

**Example:**
- If your domain is `yourdomain.com`
- Add A record: `chatbot.yourdomain.com` → `your-server-ip`
- Or use subdomain: `api.yourdomain.com` → `your-server-ip`

#### 5.2 Verify DNS Propagation

```bash
# Check DNS resolution (wait 5-10 minutes after adding)
dig chatbot.yourdomain.com
# or
nslookup chatbot.yourdomain.com
```

---

## SSL/TLS Setup with Let's Encrypt

### Step 6: Install Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Or for standalone mode
sudo apt install certbot -y
```

### Step 7: Obtain SSL Certificate

#### Option A: Using Nginx (Recommended - see Step 8 first)

```bash
# After setting up Nginx (Step 8), run:
sudo certbot --nginx -d chatbot.yourdomain.com
```

#### Option B: Standalone Mode (Before Nginx)

```bash
# Stop any service using port 80
sudo systemctl stop nginx  # if installed

# Get certificate
sudo certbot certonly --standalone -d chatbot.yourdomain.com

# Certificates will be saved to:
# /etc/letsencrypt/live/chatbot.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/chatbot.yourdomain.com/privkey.pem
```

#### 7.1 Auto-Renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renewal is usually set up automatically
# Verify cron job exists:
sudo systemctl status certbot.timer
```

---

## Reverse Proxy Setup (Nginx)

### Step 8: Install and Configure Nginx

#### 8.1 Install Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 8.2 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/edify-chatbot
```

Add the following configuration:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name chatbot.yourdomain.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name chatbot.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/chatbot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chatbot.yourdomain.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/edify-chatbot-access.log;
    error_log /var/log/nginx/edify-chatbot-error.log;

    # Client body size (for file uploads if needed)
    client_max_body_size 10M;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # WebSocket support (if needed)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (optional, for monitoring)
    location /health {
        proxy_pass http://localhost:8080/health;
        access_log off;
    }
}
```

**Important:** Replace `chatbot.yourdomain.com` with your actual domain!

#### 8.3 Enable Site and Test Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/edify-chatbot /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

#### 8.4 Get SSL Certificate (if not done in Step 7)

```bash
sudo certbot --nginx -d chatbot.yourdomain.com
```

Certbot will automatically update your Nginx configuration with SSL settings.

---

## Production Docker Compose

### Step 9: Use Production Docker Compose

Update your `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  chatbot:
    build: .
    container_name: edify-chatbot
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - PORT=8080
    # Don't expose port to host (Nginx handles it)
    # ports:
    #   - "8080:8080"
    networks:
      - chatbot-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request, os; port=os.getenv('PORT', '8080'); urllib.request.urlopen(f'http://localhost:{port}/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    # Resource limits (adjust based on your server)
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  chatbot-network:
    driver: bridge
```

Update Nginx to use Docker network:

```nginx
# In /etc/nginx/sites-available/edify-chatbot
# Change proxy_pass to:
proxy_pass http://chatbot:8080;
```

And update docker-compose.yml to connect Nginx to the network (or use host network mode).

**Simpler approach:** Keep using `localhost:8080` in Nginx if container is on host network.

### Step 10: Start Production Container

```bash
cd /opt/edify-chatbot

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chatbot

# Check if container is running
docker ps
```

---

## Monitoring and Maintenance

### Step 11: Set Up Monitoring

#### 11.1 Check Container Health

```bash
# View container logs
docker logs edify-chatbot -f

# Check container stats
docker stats edify-chatbot

# Check health endpoint
curl https://chatbot.yourdomain.com/health
```

#### 11.2 Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/edify-chatbot
```

Add:

```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
```

#### 11.3 Set Up Auto-Restart on Server Reboot

Docker Compose with `restart: unless-stopped` already handles this, but ensure Docker starts on boot:

```bash
sudo systemctl enable docker
sudo systemctl enable docker-compose  # if using systemd service
```

### Step 12: Update Application

```bash
cd /opt/edify-chatbot

# Pull latest code (if using Git)
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Or update specific service
docker-compose up -d --build chatbot
```

---

## Option B: Deploy on Cloud Platform

### Deploy on AWS EC2

1. **Launch EC2 Instance:**
   - Choose Ubuntu 20.04+ AMI
   - Configure security group: Allow ports 22, 80, 443
   - Launch instance

2. **Follow Steps 1-12** from Option A

3. **Optional: Use AWS Application Load Balancer:**
   - Create ALB
   - Point domain to ALB
   - Configure SSL certificate via AWS Certificate Manager

### Deploy on DigitalOcean

1. **Create Droplet:**
   - Choose Ubuntu 20.04+
   - Select size (2GB RAM minimum recommended)
   - Add SSH key

2. **Follow Steps 1-12** from Option A

3. **Optional: Use DigitalOcean Load Balancer**

### Deploy on Google Cloud Platform

1. **Create VM Instance:**
   - Choose Ubuntu 20.04+
   - Configure firewall rules for ports 80, 443

2. **Follow Steps 1-12** from Option A

### Deploy on Azure

1. **Create Virtual Machine:**
   - Choose Ubuntu 20.04+
   - Configure Network Security Group for ports 80, 443

2. **Follow Steps 1-12** from Option A

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs edify-chatbot

# Check if port is in use
sudo netstat -tulpn | grep 8080

# Check environment variables
docker exec edify-chatbot env
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check Nginx SSL configuration
sudo nginx -t
```

### Domain Not Resolving

```bash
# Check DNS
dig chatbot.yourdomain.com
nslookup chatbot.yourdomain.com

# Check if domain points to correct IP
curl -I http://chatbot.yourdomain.com
```

### Nginx 502 Bad Gateway

```bash
# Check if container is running
docker ps

# Check container logs
docker logs edify-chatbot

# Test if app responds on localhost
curl http://localhost:8080/health

# Check Nginx error logs
sudo tail -f /var/log/nginx/edify-chatbot-error.log
```

### High Memory Usage

```bash
# Check container resources
docker stats edify-chatbot

# Adjust memory limits in docker-compose.yml
# Restart container
docker-compose restart chatbot
```

### Application Errors

```bash
# View application logs
docker logs edify-chatbot -f --tail 100

# Check environment variables
docker exec edify-chatbot printenv | grep -E "OPENAI|SUPABASE|ENV"

# Restart container
docker-compose restart chatbot
```

---

## Quick Reference Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f chatbot

# Restart application
docker-compose restart chatbot

# Rebuild and restart
docker-compose up -d --build

# Check status
docker-compose ps

# Access container shell
docker exec -it edify-chatbot sh

# Update application
git pull && docker-compose up -d --build

# Check SSL certificate expiry
sudo certbot certificates

# Renew SSL certificate
sudo certbot renew
```

---

## Security Checklist

- [ ] Firewall configured (ports 22, 80, 443 only)
- [ ] SSL/TLS certificate installed and auto-renewal enabled
- [ ] Environment variables secured (`.env` file permissions)
- [ ] CORS configured with specific domains
- [ ] Rate limiting enabled
- [ ] Regular security updates applied
- [ ] Strong SSH key authentication
- [ ] Docker container running as non-root user (optional)
- [ ] Logs monitored regularly
- [ ] Backups configured (database, environment variables)

---

## Support

For issues or questions:
1. Check application logs: `docker logs edify-chatbot`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/edify-chatbot-error.log`
3. Verify environment variables are set correctly
4. Test health endpoint: `curl https://chatbot.yourdomain.com/health`

---

**Congratulations!** Your Edify Chatbot Agent should now be accessible at `https://chatbot.yourdomain.com` 🎉

