# 🚀 Hướng Dẫn Deploy Amazon Feedback AI Agent

## 📋 Mục lục
1. [Deploy Local (Để test)](#1-deploy-local)
2. [Deploy trên VPS/Server (Ubuntu/Linux)](#2-deploy-trên-vps)
3. [Deploy lên Cloud (Railway, Render, DigitalOcean)](#3-deploy-lên-cloud)
4. [Cấu hình Domain & SSL](#4-cấu-hình-domain--ssl)

---

## 1. Deploy Local

### Chuẩn bị
```bash
# Đã làm rồi - chỉ cần chạy:
cd C:\Users\Admin\OneDrive\Desktop\Amazon\amazon-feedback-ai-agent

# Terminal 1 - Backend
python api.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

Truy cập: `http://localhost:3000`

---

## 2. Deploy trên VPS (Ubuntu/Linux)

### Bước 1: Chuẩn bị VPS
```bash
# SSH vào server
ssh root@your-server-ip

# Update hệ thống
sudo apt update && sudo apt upgrade -y

# Cài Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# Cài Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Cài Nginx (web server)
sudo apt install nginx -y

# Cài PM2 (process manager)
sudo npm install -g pm2
```

### Bước 2: Upload Code lên Server
```bash
# Trên máy local - Zip code
# (Loại bỏ node_modules, __pycache__, .env)

# Upload lên server (dùng SCP hoặc Git)
# Cách 1: Dùng Git
ssh root@your-server-ip
git clone https://github.com/quanho114/amazon-feedback-ai-agent.git
cd amazon-feedback-ai-agent

# Cách 2: Dùng SCP từ máy local
scp -r C:\Users\Admin\OneDrive\Desktop\Amazon\amazon-feedback-ai-agent root@your-server-ip:/var/www/
```

### Bước 3: Cài Dependencies
```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build  # Build production
```

### Bước 4: Tạo file .env
```bash
nano .env
```
```env
MEGALLM_API_KEY=your_key_here
MEGALLM_BASE_URL=https://api.mega-llm.com/v1
MEGALLM_MODEL=gpt-4
```

### Bước 5: Chạy với PM2
```bash
# Backend (FastAPI)
pm2 start "uvicorn api:app --host 0.0.0.0 --port 8000" --name backend

# Frontend (Serve build folder)
cd frontend
pm2 serve dist 3000 --name frontend --spa

# Lưu config PM2
pm2 save
pm2 startup

# Kiểm tra status
pm2 status
pm2 logs backend
```

### Bước 6: Cấu hình Nginx Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/amazon-ai
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Hoặc IP server

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Kích hoạt site
sudo ln -s /etc/nginx/sites-available/amazon-ai /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Bước 7: Mở Firewall
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22  # SSH
sudo ufw enable
```

✅ Truy cập: `http://your-server-ip` hoặc `http://your-domain.com`

---

## 3. Deploy lên Cloud

### A. Railway.app (Dễ nhất - Free tier)

1. **Tạo tài khoản**: https://railway.app
2. **New Project → Deploy from GitHub**
3. **Chọn repo**: `quanho114/amazon-feedback-ai-agent`
4. **Thêm 2 services**:

**Service 1 - Backend:**
```bash
# Start Command
uvicorn api:app --host 0.0.0.0 --port $PORT

# Environment Variables
MEGALLM_API_KEY=your_key
MEGALLM_BASE_URL=https://api.mega-llm.com/v1
MEGALLM_MODEL=gpt-4
```

**Service 2 - Frontend:**
```bash
# Build Command
cd frontend && npm install && npm run build

# Start Command  
npm install -g serve && serve -s frontend/dist -l $PORT

# Environment Variables
VITE_API_URL=https://your-backend.railway.app
```

5. **Deploy** → Nhận URL public: `https://your-app.railway.app`

---

### B. Render.com (Free tier)

1. **Tạo Web Service** cho Backend:
```yaml
Build Command: pip install -r requirements.txt
Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
```

2. **Tạo Static Site** cho Frontend:
```yaml
Build Command: cd frontend && npm install && npm run build
Publish Directory: frontend/dist
```

---

### C. DigitalOcean App Platform ($5/tháng)

1. **Create App → From GitHub**
2. **Backend component:**
   - Type: Web Service
   - Run Command: `uvicorn api:app --host 0.0.0.0 --port 8080`
   - HTTP Port: 8080

3. **Frontend component:**
   - Type: Static Site
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`

---

## 4. Cấu hình Domain & SSL

### Với Nginx + Certbot (Free SSL)
```bash
# Cài Certbot
sudo apt install certbot python3-certbot-nginx -y

# Lấy SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renew
sudo certbot renew --dry-run
```

### Update Nginx với SSL:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Rest của config...
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 5. Monitoring & Maintenance

### Xem logs
```bash
# PM2 logs
pm2 logs backend
pm2 logs frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart services
```bash
pm2 restart backend
pm2 restart frontend
sudo systemctl restart nginx
```

### Update code
```bash
cd /var/www/amazon-feedback-ai-agent
git pull origin main

# Rebuild frontend
cd frontend
npm run build

# Restart
pm2 restart all
```

---

## 6. Checklist Deploy

- [ ] Code đã push lên GitHub
- [ ] File `.env` có đầy đủ API keys
- [ ] `requirements.txt` có đủ dependencies
- [ ] Frontend build thành công (`npm run build`)
- [ ] Backend chạy được (`uvicorn api:app`)
- [ ] Database/Vector store có data
- [ ] CORS cho phép domain mới
- [ ] Firewall mở port 80, 443
- [ ] SSL certificate đã cài (HTTPS)
- [ ] PM2 auto-restart khi server reboot
- [ ] Logs được monitor

---

## 7. Chi phí Ước tính

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Railway | 500 giờ/tháng | $5-20/tháng |
| Render | 750 giờ/tháng | $7-25/tháng |
| DigitalOcean | N/A | $5-10/tháng |
| VPS (Vultr/Linode) | N/A | $5-10/tháng |
| Domain (.com) | N/A | $10-15/năm |
| SSL | Free (Let's Encrypt) | Free |

---

## 8. Tips Bảo mật

1. **Đổi SSH port** mặc định (22 → 2222)
2. **Tắt SSH login bằng password** → Chỉ dùng SSH key
3. **Cài fail2ban** chống brute force
4. **Set rate limiting** trên Nginx
5. **Backup database** hàng ngày
6. **Monitor disk space**: `df -h`
7. **Update hệ thống** định kỳ

```bash
# Cài fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

---

## Cần hỗ trợ?

- GitHub: https://github.com/quanho114/amazon-feedback-ai-agent
- Issues: Tạo issue trên GitHub repo

🎉 Chúc deploy thành công!
