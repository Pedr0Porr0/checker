# Checker - Leaksyr API 2.0.0 Integration

Proyecto Python para integración, monitoreo y búsqueda en la **API Leaksyr 2.0.0** - Base de datos de brechas de seguridad con 12+ mil millones de registros.

## 🎯 Características Principales

✅ Cliente completo para API Leaksyr 2.0.0  
✅ Búsqueda por dominio (family/exact/fuzzy)  
✅ Búsqueda por usuario/email  
✅ Búsqueda de cookies y sesiones (Business-tier)  
✅ Monitoreo de salud y disponibilidad de API  
✅ Soporte para paginación, filtros de fecha e idempotencia  
✅ Ejemplos completos y documentación  

---

## 📋 API Endpoints Soportados

| Endpoint | Descripción | Disponibilidad |
|----------|-------------|-----------------|
| `GET /api/health` | Health check | Todos |
| `GET /api/v2/search` | Búsqueda por dominio | Todos |
| `GET /api/v2/search/username` | Búsqueda exacta de usuario | Todos |
| `GET /api/v2/search/email` | Búsqueda exacta de email | Todos |
| `GET /api/v2/search/cookies` | Búsqueda de cookies | Business-tier ⭐ |
| `GET /api/v2/search/cookies/{id}/related` | Cookies relacionadas | Business-tier ⭐ |

---

## 🚀 Inicio Rápido

### 1. Configuración

```bash
# Clonar/descargar el proyecto
cd checker

# Crear archivo .env
cp .env.example .env

# Editar .env y agregar tu API Key
# LEAKSYR_API_KEY=lk_2txIsaJyaIEe6sV0LH5O6QyPjWvRgb7G8Ut0J9x5QVs
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Prueba de Conexión

```bash
python quick_test.py
```

### 4. Ver Ejemplos

```bash
python examples.py
```

---

## 💻 Uso Básico

### Importar y Conectar

```python
from checker.api_client import LeaksyrClient

# Inicializar cliente
client = LeaksyrClient()  # Usa API_KEY de .env
```

### Búsqueda por Dominio

```python
# Familia (todos los subdomios)
result = client.search_domain(
    domain="google.com",
    match_mode="family",
    limit=10
)
print(f"Encontrados: {result['meta']['count']} registros")

# Exacto (host único)
result = client.search_domain(
    domain="mail.google.com",
    match_mode="exact"
)

# Fuzzy (substring)
result = client.search_domain(
    domain="google",
    match_mode="fuzzy"
)
```

### Búsqueda por Usuario/Email

```python
# Por usuario (exacta)
result = client.search_username("admin")

# Por email (exacta)
result = client.search_email("user@example.com")

print(f"Registros encontrados: {result['meta']['count']}")
```

### Búsqueda de Cookies (Business-tier)

```python
# Buscar cookies por dominio
result = client.search_cookies(
    domain="facebook.com",
    match_mode="family"
)

# Obtener cookies relacionadas (misma sesión)
result = client.get_related_cookies(cookie_id="abc123")
print(f"Cookies de la sesión: {result['meta']['count']}")
```

### Paginación

```python
# Página 1
result = client.search_domain("example.com", limit=50, offset=0)

# Página 2
result = client.search_domain("example.com", limit=50, offset=50)

# Verificar si hay más páginas
if result['meta']['has_more']:
    print("Hay más resultados disponibles")
```

### Filtrar por Fechas

```python
result = client.search_domain(
    domain="example.com",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### Idempotencia

```python
# Garantiza que la misma solicitud devuelve el mismo resultado
result = client.search_domain(
    domain="example.com",
    idempotency_key="my-unique-id-12345"
)
```

---

## 📁 Estructura del Proyecto

```
checker/
├── README.md                    # Este archivo
├── API_DOCS.md                  # Documentación completa de endpoints
├── requirements.txt             # Dependencias Python
├── .env.example                 # Template de configuración
│
├── quick_test.py                # Script de prueba rápida
├── examples.py                  # Ejemplos de uso de todos los endpoints
│
├── checker/
│   ├── __init__.py
│   ├── api_client.py            # LeaksyrClient - Cliente principal
│   └── health.py                # HealthChecker - Monitor de salud
│
└── tests/
    └── test_api.py              # Tests unitarios
```

---

## 🔐 Configuración de Autenticación

### Archivo .env

```
# Leaksyr API Configuration
LEAKSYR_API_KEY=lk_2txIsaJyaIEe6sV0LH5O6QyPjWvRgb7G8Ut0J9x5QVs
LEAKSYR_BASE_URL=https://leaksyr.com/api
```

El cliente lee automáticamente de `.env` usando `python-dotenv`.

### Header de Autenticación

Internamente, todas las solicitudes incluyen:
```
Authorization: Bearer <API_KEY>
```

---

## 📊 Estructura de Respuesta

### Respuesta Exitosa (200)

```json
{
  "success": true,
  "meta": {
    "query": "google.com",
    "count": 1234,
    "limit": 50,
    "offset": 0,
    "sort": "desc",
    "has_more": true,
    "sandbox": false,
    "daily_requests_remaining": 9950,
    "api_version": "2.0.0"
  },
  "data": [
    { /* registros encontrados */ }
  ]
}
```

### Error de Validación (422)

```json
{
  "detail": [
    {
      "loc": ["query", 0],
      "msg": "String should have at least 3 characters",
      "type": "string_too_short",
      "input": "go",
      "ctx": { "min_length": 3 }
    }
  ]
}
```

---

## ⚙️ Parámetros Detallados

### Búsqueda por Dominio - Modos Match

| Modo | Ejemplo | Comportamiento |
|------|---------|-----------------|
| **family** | `google.com` | `google.com` + todos sus subdomios (`mail.google.com`, `docs.google.com`, etc.) |
| **exact** | `mail.google.com` | Solo ese host exacto |
| **fuzzy** | `mail` | Substring en `cookie_domain` o `cookie_name` |

### Parámetros Comunes

- **`limit`**: Máximo 50 resultados por página (default: 50)
- **`offset`**: Saltar N resultados para pagination (default: 0)
- **`sort`**: `asc` (ascendente) o `desc` (descendente, default)
- **`start_date`/`end_date`**: Formato YYYY-MM-DD
- **`X-Idempotency-Key`**: Header para garantizar idempotencia

---

## 🧪 Testing

### Tests Unitarios

```bash
pytest tests/test_api.py -v
```

### Ejecución Manual

```bash
# Health check
python -c "from checker.api_client import LeaksyrClient; c = LeaksyrClient(); print(c.health_check())"

# Búsqueda simple
python -c "from checker.api_client import LeaksyrClient; c = LeaksyrClient(); r = c.search_domain('google.com', limit=5); print(f'Encontrados: {r[\"meta\"][\"count\"]}')"
```

---

## 📚 Documentación Adicional

- **[API_DOCS.md](API_DOCS.md)** - Documentación completa de endpoints
- **[examples.py](examples.py)** - Ejemplos de uso de todas las funciones
- **[checker/api_client.py](checker/api_client.py)** - Código fuente con docstrings

---

## 📝 Notas Importantes

### Validación de Entrada

- Mínimo 3 caracteres en query
- Máximo 253-254 caracteres
- URLs válidas para búsqueda por dominio

### Cuotas

- El servidor limita a **50 resultados por página máximo**
- Se monitorea `daily_requests_remaining` en cada respuesta
- Usa paginación para obtener más resultados

### Business-Tier

Los endpoints de **cookies** (`/search/cookies` y `/search/cookies/{id}/related`) requieren una API Key de Business-tier.

---

## 🔄 Respuesta Estándar - Campos Meta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `query` | string | Query ejecutada |
| `count` | integer | Resultados en esta página |
| `limit` | integer | Límite solicitado |
| `offset` | integer | Offset usado |
| `sort` | string | Orden de resultados |
| `has_more` | boolean | ¿Hay más páginas? |
| `sandbox` | boolean | ¿Modo sandbox? |
| `daily_requests_remaining` | integer | Requests restantes hoy |
| `api_version` | string | Versión de API usada |

---

## 🛠️ Dependencias

- **requests** - Cliente HTTP
- **python-dotenv** - Manejo de variables de entorno
- **pydantic** - Validación de datos (futuro)
- **pytest** - Testing
- **pytest-asyncio** - Tests asincronos

---

## 📌 Roadmap

- [ ] Dashboard web interactivo
- [ ] Sistema de alertas para dominios monitoreados
- [ ] Exportación a CSV/JSON/PDF
- [ ] CLI mejorada con comandos avanzados
- [ ] Cache local de búsquedas
- [ ] Integración con SIEM (Splunk, ELK, etc.)
- [ ] API GraphQL
- [ ] Webhooks para notificaciones

---

## 📧 Contacto & Soporte

- **API Docs**: https://leaksyr.com/api/docs
- **OpenAPI Spec**: https://leaksyr.com/api/openapi.json

---

**Última actualización**: 2026-08-22  
**Versión**: 1.0.0  
**API Version**: 2.0.0  
**Estado**: 🟢 Producción

