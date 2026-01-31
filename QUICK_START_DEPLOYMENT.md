# ⚡ Quick Start Deployment Guide

This is a condensed version. For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🎯 5-Minute Overview

1. **Get a server** (VPS/Cloud) with Ubuntu 20.04+
2. **Install Docker** on the server
3. **Upload your code** to the server
4. **Configure domain** DNS to point to server IP
5. **Set up Nginx** as reverse proxy
6. **Get SSL certificate** with Let's Encrypt
7. **Deploy application** with Docker Compose

---

## 📝 Step-by-Step (Condensed)

### 1. Server Setup

```bash
# Connect to server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Upload Code

```bash
# On server, create directory
sudo mkdir -p /opt/edify-chatbot
cd /opt/edify-chatbot

# Upload files (use Git, SCP, or rsync)
git clone https://your-repo-url.git .
# OR
# scp -r . user@server:/opt/edify-chatbot/
```

### 3. Configure Environment

```bash
cd /opt/edify-chatbot
nano .env
```

Add all required variables (see DEPLOYMENT.md for full list).

### 4. Configure DNS

At your domain registrar, add:
- **Type:** A Record
- **Name:** `chatbot` (or subdomain of choice)
- **Value:** Your server IP address
- **TTL:** 3600

Wait 5-10 minutes for DNS propagation.

### 5. Install Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 6. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/edify-chatbot
```

Copy configuration from `nginx/edify-chatbot.conf` (update domain name).

```bash
sudo ln -s /etc/nginx/sites-available/edify-chatbot /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Get SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d chatbot.yourdomain.com
```

### 8. Deploy Application

```bash
cd /opt/edify-chatbot
docker-compose -f docker-compose.prod.yml up -d
```

### 9. Verify

```bash
# Check container
docker ps

# Check logs
docker logs edify-chatbot

# Test health
curl https://chatbot.yourdomain.com/health
```

---

## ✅ Verification Checklist

- [ ] Container is running: `docker ps`
- [ ] Health endpoint works: `curl https://chatbot.yourdomain.com/health`
- [ ] SSL certificate is valid (green lock in browser)
- [ ] Application accessible at your domain
- [ ] Logs show no errors: `docker logs edify-chatbot`

---

## 🔧 Common Commands

```bash
# View logs
docker logs edify-chatbot -f

# Restart application
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Check SSL certificate
sudo certbot certificates
```

---

## 🆘 Quick Troubleshooting

**Container won't start?**
```bash
docker logs edify-chatbot
```

**502 Bad Gateway?**
```bash
# Check if container is running
docker ps

# Check if app responds
curl http://localhost:8080/health
```

**SSL issues?**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

For detailed instructions, troubleshooting, and advanced configuration, see [DEPLOYMENT.md](DEPLOYMENT.md).

