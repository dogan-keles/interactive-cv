# Gemini Setup Guide

## Google Gemini API Key Alma

1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine git
2. "Get API Key" butonuna tıkla
3. Google hesabınla giriş yap
4. Yeni bir API key oluştur
5. API key'i kopyala

## Kurulum

### 1. Dependencies

```bash
pip install google-generativeai
```

veya `requirements.txt` ile:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

`.env` dosyasına ekle:

```env
GEMINI_API_KEY=your-api-key-here
LLM_MODEL=gemini-pro
```

## Kullanılabilir Modeller

- **gemini-pro** - Genel kullanım için (önerilen)
- **gemini-pro-vision** - Görüntü analizi için
- **gemini-1.5-pro** - Daha güçlü, daha yavaş
- **gemini-1.5-flash** - Daha hızlı, daha küçük

## Özellikler

✅ **Ücretsiz tier** - Sınırlı ama yeterli
✅ **Hızlı** - Düşük latency
✅ **İyi kalite** - Google'ın en iyi modelleri
✅ **Türkçe desteği** - İyi Türkçe anlama ve üretme

## Rate Limits

Gemini API'nin ücretsiz tier'ında:
- **15 RPM** (Requests Per Minute)
- **1,500,000 TPM** (Tokens Per Minute)

Production için yeterli.

## Test

```bash
# Health check
curl http://localhost:8000/health

# Chat test
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the candidate'\''s skills?",
    "profile_id": 1
  }'
```

## Sorun Giderme

### API Key hatası
- API key'in doğru olduğundan emin ol
- `.env` dosyasında `GEMINI_API_KEY` olduğunu kontrol et

### Rate limit hatası
- Çok fazla request gönderiyorsun
- Rate limit'i aşmamak için request'leri throttle et

### Model bulunamadı
- Model adını kontrol et (`gemini-pro`, `gemini-1.5-pro`, vs.)
- Google AI Studio'da model'in mevcut olduğunu kontrol et

## Deployment

Docker Compose ile deploy ederken:

```env
GEMINI_API_KEY=your-api-key
LLM_MODEL=gemini-pro
```

`docker-compose.yml`'de environment variables otomatik olarak geçer.




