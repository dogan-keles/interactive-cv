# Deployment Guide - Ollama ile Production

## Docker ile Deploy

### 1. Hızlı Başlangıç

```bash
# Tüm servisleri başlat (PostgreSQL + Ollama + Backend)
docker-compose up -d

# Ollama model indir (ilk kez)
docker-compose exec ollama ollama pull llama3

# Logları izle
docker-compose logs -f backend
```

### 2. Servisler

- **PostgreSQL**: `localhost:5432`
- **Ollama**: `localhost:11434`
- **Backend API**: `localhost:8000`

### 3. Environment Variables

`.env` dosyası oluştur (opsiyonel, docker-compose.yml'deki varsayılanlar kullanılır):

```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=interactive_cv
LLM_MODEL=llama3
```

## Production Deployment

### Seçenek 1: VPS/Cloud Server (AWS, DigitalOcean, Hetzner, vs.)

#### 1.1 Server Setup

```bash
# Docker ve Docker Compose kur
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose kur
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 1.2 Projeyi Deploy Et

```bash
# Projeyi clone et
git clone <your-repo>
cd interactice-cv

# Environment variables ayarla
cp .env.example .env
nano .env  # Düzenle

# Servisleri başlat
docker-compose up -d

# Model indir
docker-compose exec ollama ollama pull llama3

# Database migration (gerekirse)
docker-compose exec backend python -c "from data_access.knowledge_base.postgres import Base; from infrastructure.database import engine; Base.metadata.create_all(bind=engine)"
```

#### 1.3 Nginx Reverse Proxy (Önerilen)

```nginx
# /etc/nginx/sites-available/interactive-cv
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/interactive-cv /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Seçenek 2: Railway / Render / Fly.io

Bu platformlar Docker Compose'u destekler. `docker-compose.yml` dosyasını kullanabilirsin.

**Railway:**
1. Railway'e git
2. New Project → Deploy from GitHub
3. `docker-compose.yml` otomatik algılanır
4. Environment variables ekle

**Render:**
1. Render'da Docker service oluştur
2. `docker-compose.yml` kullan
3. Environment variables ayarla

### Seçenek 3: Kubernetes

Daha büyük ölçekli deployment için Kubernetes manifest'leri hazırlanabilir.

## GPU Desteği (Opsiyonel)

Ollama GPU ile çok daha hızlı çalışır:

### NVIDIA GPU

```yaml
# docker-compose.yml'de zaten var
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Gereksinimler:**
- NVIDIA GPU
- nvidia-docker2 kurulu
- NVIDIA Container Toolkit

```bash
# NVIDIA Container Toolkit kur
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### CPU-Only (GPU Yoksa)

`docker-compose.yml`'den `deploy` kısmını kaldır. Ollama CPU'da da çalışır, sadece daha yavaş olur.

## Model Yönetimi

### Model İndirme

```bash
# Container içinde
docker-compose exec ollama ollama pull llama3

# Veya host'tan
docker exec <ollama-container-id> ollama pull llama3
```

### Model Listeleme

```bash
docker-compose exec ollama ollama list
```

### Model Silme

```bash
docker-compose exec ollama ollama rm llama3
```

## Monitoring ve Logs

### Logları İzle

```bash
# Tüm servisler
docker-compose logs -f

# Sadece backend
docker-compose logs -f backend

# Sadece Ollama
docker-compose logs -f ollama
```

### Health Check

```bash
# Backend
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags
```

### Resource Kullanımı

```bash
docker stats
```

## Scaling

### Backend Scaling

```bash
# Birden fazla backend instance
docker-compose up -d --scale backend=3
```

### Load Balancer

Nginx veya Traefik ile load balancing yapılabilir.

## Backup

### Database Backup

```bash
docker-compose exec postgres pg_dump -U user interactive_cv > backup.sql
```

### Ollama Models Backup

```bash
# Models volume'da saklanır
docker run --rm -v interactice-cv_ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama_backup.tar.gz /data
```

## Troubleshooting

### Ollama bağlanamıyor

```bash
# Ollama çalışıyor mu?
docker-compose ps ollama

# Logları kontrol et
docker-compose logs ollama

# Yeniden başlat
docker-compose restart ollama
```

### Model bulunamadı

```bash
# Model listesi
docker-compose exec ollama ollama list

# Model yoksa indir
docker-compose exec ollama ollama pull llama3
```

### Memory yetersiz

Ollama modelleri RAM kullanır. Küçük model kullan:
```bash
docker-compose exec ollama ollama pull gemma:2b
```

## Cost Optimization

1. **Küçük model kullan**: `gemma:2b` veya `llama3:8b`
2. **CPU-only**: GPU yoksa CPU kullan (daha yavaş ama ücretsiz)
3. **Auto-scaling**: Kullanım yoksa servisleri durdur
4. **Caching**: Response'ları cache'le

## Security

1. **Environment variables**: `.env` dosyasını git'e commit etme
2. **Firewall**: Sadece gerekli portları aç
3. **HTTPS**: Nginx ile SSL/TLS ekle
4. **Database**: Güçlü password kullan

## Örnek Production Setup

```bash
# 1. Server'a bağlan
ssh user@your-server.com

# 2. Projeyi clone et
git clone <repo>
cd interactice-cv

# 3. Environment ayarla
cp .env.example .env
nano .env

# 4. Deploy
docker-compose up -d

# 5. Model indir
docker-compose exec ollama ollama pull llama3

# 6. Database setup
docker-compose exec backend python -c "from data_access.knowledge_base.postgres import Base; from infrastructure.database import engine; Base.metadata.create_all(bind=engine)"

# 7. Test
curl http://localhost:8000/health
```

Sistem production'da çalışmaya hazır! 🚀



