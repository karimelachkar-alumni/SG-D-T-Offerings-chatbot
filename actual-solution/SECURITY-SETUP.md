# 🔐 Security Setup Guide

## ⚠️ CRITICAL: API Keys Were Exposed

Your API keys were previously exposed in the `.env` file. **You must immediately:**

1. **Revoke the exposed API keys** from their respective services:

   - Google API Key: `AIzaSyBAnP5-F2tVaHoNtkMkCfBXLky_nDmZwVs`
   - Groq API Key: `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`

2. **Generate new API keys** from:
   - [Google AI Studio](https://makersuite.google.com/app/apikey)
   - [Groq Console](https://console.groq.com/keys)

## 🛡️ Security Measures Implemented

### ✅ Environment Variables

- All sensitive configuration moved to `.env` file
- `.env` file is properly excluded from Git via `.gitignore`
- Hardcoded secrets removed from source code

### ✅ Configuration Files

- `.env.example` provides template for required environment variables
- All API keys now use environment variable loading
- Flask SECRET_KEY now uses environment variable

## 🚀 Setup Instructions

### 1. Create Your Environment File

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual API keys
nano .env  # or use your preferred editor
```

### 2. Add Your API Keys

Edit `.env` and replace the placeholder values:

```bash
# Google Gemini Configuration
GOOGLE_API_KEY=your_actual_google_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Groq Configuration (Fallback)
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Security - Generate a strong random key
SECRET_KEY=your-strong-random-secret-key-here
```

### 3. Generate a Strong Secret Key

```bash
# Option 1: Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Option 3: Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

## 🔒 Security Best Practices

### ✅ Do's

- ✅ Keep `.env` file local only
- ✅ Use strong, unique secret keys
- ✅ Regularly rotate API keys
- ✅ Use environment-specific configurations
- ✅ Monitor API key usage

### ❌ Don'ts

- ❌ Never commit `.env` files to Git
- ❌ Never share API keys in chat/email
- ❌ Never use the same keys across environments
- ❌ Never hardcode secrets in source code

## 🚨 Emergency Response

If you suspect your API keys are compromised:

1. **Immediately revoke** the compromised keys
2. **Generate new keys** from the service providers
3. **Update your `.env` file** with new keys
4. **Review access logs** for any unauthorized usage
5. **Consider rotating all related credentials**

## 📋 Verification Checklist

- [ ] `.env` file exists and contains your API keys
- [ ] `.env` file is NOT tracked by Git
- [ ] `.env.example` exists with placeholder values
- [ ] No hardcoded secrets in source code
- [ ] Application runs with environment variables
- [ ] Old exposed keys have been revoked

## 🔧 Troubleshooting

### Application won't start

```bash
# Check if .env file exists
ls -la .env

# Verify environment variables are loaded
python -c "from config.settings import settings; print('API keys loaded:', bool(settings.google_api_key))"
```

### Environment variables not loading

```bash
# Check .env file format (no spaces around =)
cat .env | grep -E "^\s*[A-Z_]+="

# Verify .env file is in the correct directory
pwd && ls -la .env
```

## 📞 Support

If you need help with security setup or have concerns about exposed credentials, please contact your system administrator or security team immediately.
