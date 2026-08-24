# DEPLOYMENT GUIDE - Checker API

## ⚠️ IMPORTANTE

Este proyecto es un **Backend FastAPI + Frontend SPA**. 

- **Netlify** = solo para sitios estáticos (no funciona con FastAPI)
- **Render/Railway/Heroku** = perfectos para FastAPI

---

## OPCIÓN 1: Deploy en Render.com ⭐ RECOMENDADO

Render.com soporta Python/FastAPI perfectamente y es gratuito.

### Pasos:

1. **Crea cuenta en Render.com** (gratuito)
   - https://render.com

2. **Conecta GitHub a Render**
   - Dashboard → New Web Service
   - Connect your GitHub account
   - Selecciona tu repositorio

3. **Render leerá `render.yaml` automáticamente**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn web_server:app --host 0.0.0.0 --port $PORT`
   - Python Version: 3.14

4. **Agrega variables de entorno en Render**
   - Environment → Add Environment Variable
   - `LEAKSYR_API_KEY` = tu API key
   - `SHODAN_API_KEY` = (opcional)
   - `CENSYS_API_KEY` = (opcional)

5. **Deploy automático**
   - Cada push a GitHub = auto-deploy
   - URL final: `https://checker-api-xxxx.onrender.com`

---

## OPCIÓN 2: Deploy en Railway.app

Railway también soporta FastAPI con deploy automático.

### Pasos:

1. https://railway.app
2. New Project → GitHub Repo
3. Add variables de entorno
4. Auto-deploy en cada push

---

## OPCIÓN 3: Frontend en Netlify + Backend en Render (ADVANCED)

Si quieres separar frontend y backend:

1. **Backend en Render** (instrucciones arriba)
2. **Frontend en Netlify:**
   - Extrae HTML de `web_server.py`
   - Crea carpeta `/frontend` con archivos estáticos
   - Actualiza URLs de API para apuntar a Render
   - Sube a Netlify

---

## Configuración de Variables de Entorno

### En Render.com:
Dashboard → Environment Variables

```
LEAKSYR_API_KEY=tu_api_key_aqui
SHODAN_API_KEY=opcional
CENSYS_API_KEY=opcional
CENSYS_API_SECRET=opcional
```

### En Railway.app:
Variables → Add Variable

### Localmente (desarrollo):
Copia `.env.example` a `.env`:
```bash
cp .env.example .env
# Edita .env con tus claves
```

---

## Troubleshooting

### Error: ModuleNotFoundError: No module named 'fastapi'
✅ Solucionado - `requirements.txt` actualizado con todas las dependencias

### Error: Port already in use
- Render/Railway asignan puerto automáticamente
- No necesitas especificar puerto en el código

### Error: API key no válida
1. Verifica la key en variables de entorno
2. Reinicia la aplicación después de agregar env vars
3. En local: revisa que `.env` esté bien

### Deploy lento en Render (plan gratuito)
- Plan Free = servidor se detiene si no hay tráfico por 15 min
- Upgrade a plan pagado para servidor siempre activo
- O usa Railway (mejor para free tier)

---

## Estructura del Proyecto

```
CHECKER_NETLIFY/
├── web_server.py              # FastAPI app (puerto dinámico)
├── requirements.txt           # Todas las dependencias ✅
├── README.md                  # Docs
├── .gitignore                 # No commits de claves
├── .env.example               # Template variables
├── render.yaml                # Config para Render ⭐
├── netlify.toml               # Config para Netlify (frontend)
├── DEPLOYMENT.md              # Este archivo
└── checker/                   # Python package
    ├── api_client.py
    ├── osint_integrations.py  # 50+ OSINT sources
    └── health.py
```

---

## Pasos Rápidos para Deploy

### 1. Inicializa Git:
```bash
cd CHECKER_NETLIFY
git init
git add .
git commit -m "Initial commit - Checker API"
git remote add origin https://github.com/tusuario/checker.git
git push -u origin main
```

### 2. Deploy en Render:
- Ve a https://render.com
- New Web Service
- Conecta tu GitHub
- Render leerá `render.yaml` automáticamente
- Deploy ✅

### 3. Test tu API:
```bash
# Una vez deployado en Render
curl https://checker-api-xxxx.onrender.com/

# Debe devolver la página web del Checker
```

---

## URLs de Deploy

**Render.com:**
```
https://checker-api-xxxx.onrender.com/
https://checker-api-xxxx.onrender.com/api/simple-search?field=domain&query=example.com
```

**Railway:**
```
https://checker-xxxx.up.railway.app/
```

**Netlify (solo frontend):**
```
https://checker-xxxxx.netlify.app/
```

---

## Importante ⚠️

**NUNCA commits tus API keys**
- `.env` está en `.gitignore` (protegido)
- Usa siempre variables de entorno en producción
- Render/Railway tienen interfaz para agregar variables seguramente

---

## ¿Preguntas?

1. **¿Qué tan rápido es?** - Render/Railway arrancan en 5-10 segundos
2. **¿Cuánto cuesta?** - Gratuito con límites generosos (Railway es mejor para free tier)
3. **¿Puedo actualizar código?** - Sí, cada push a GitHub = auto-deploy

¡Listo! 🚀

