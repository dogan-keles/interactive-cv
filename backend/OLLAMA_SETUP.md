# Ollama Setup Guide (Ücretsiz LLM)

## Ollama Nedir?

Ollama, yerel makinenizde çalışan, tamamen ücretsiz bir LLM server'ıdır. OpenAI API'ye ihtiyaç duymaz.

## Kurulum

### 1. Ollama'yı İndir ve Kur

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
[Ollama.com](https://ollama.com) adresinden indir.

### 2. Ollama'yı Başlat

```bash
ollama serve
```

Bu komut Ollama'yı `http://localhost:11434` adresinde çalıştırır.

### 3. Model İndir

Popüler ücretsiz modeller:

```bash
# Llama 3 (8B - Önerilen, hızlı ve iyi)
ollama pull llama3

# Mistral (7B - Alternatif)
ollama pull mistral

# Qwen (7B - Çok iyi Türkçe desteği)
ollama pull qwen2.5

# Gemma (2B - Çok küçük, hızlı)
ollama pull gemma:2b
```

**Öneri:** `llama3` veya `qwen2.5` (Türkçe için daha iyi)

### 4. Environment Variables

`.env` dosyasına ekle:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3
```

## Kullanım

Sistem otomatik olarak Ollama'yı kullanacak. Başka bir şey yapmana gerek yok!

## Model Karşılaştırması

| Model | Boyut | Hız | Kalite | Türkçe |
|-------|-------|-----|--------|--------|
| llama3 | 8B | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| qwen2.5 | 7B | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| mistral | 7B | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| gemma:2b | 2B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

## Sorun Giderme

### Ollama bağlantı hatası
```bash
# Ollama çalışıyor mu kontrol et
curl http://localhost:11434/api/tags

# Çalışmıyorsa başlat
ollama serve
```

### Model bulunamadı
```bash
# İndirilmiş modelleri listele
ollama list

# Model yoksa indir
ollama pull llama3
```

### Yavaş çalışıyor
- Daha küçük model kullan (gemma:2b)
- GPU varsa Ollama otomatik kullanır
- CPU'da çalışıyorsa daha yavaş olabilir

## OpenAI'ye Geri Dönmek İstersen

`.env` dosyasında:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
LLM_MODEL=gpt-3.5-turbo
```

## Avantajlar

✅ **Tamamen ücretsiz** - Hiçbir API key gerekmez
✅ **Gizlilik** - Veriler yerel kalır, internete gönderilmez
✅ **Sınırsız kullanım** - Rate limit yok
✅ **Offline çalışır** - İnternet bağlantısı gerekmez

## Dezavantajlar

⚠️ **Yerel kaynak kullanır** - RAM ve CPU kullanır
⚠️ **İlk kurulum gerekir** - Ollama ve model indirmek gerekir
⚠️ **OpenAI kadar hızlı değil** - Özellikle CPU'da




