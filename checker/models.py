"""Pydantic models basados en OpenAPI spec de Leaksyr 2.0.0"""

from typing import Optional, Any, Dict, List
from datetime import date
from pydantic import BaseModel, Field, field_validator


# ========== Respuestas ==========

class SearchMeta(BaseModel):
    """Metadata de búsqueda"""
    query: str
    count: int
    limit: int
    offset: int
    sort: str
    has_more: Optional[bool] = None
    sandbox: Optional[bool] = None
    daily_requests_remaining: int
    api_version: str


class SearchResponse(BaseModel):
    """Respuesta estándar de búsqueda"""
    success: bool = True
    meta: SearchMeta
    data: List[Dict[str, Any]]


class CookieDetailMeta(BaseModel):
    """Metadata de detalle de cookie"""
    cookie_id: str
    source_id: Optional[str] = None
    cookie_etld1: Optional[str] = None
    cookie_domain: Optional[str] = None
    count: int
    distinct_domains: int
    sandbox: Optional[bool] = None
    daily_requests_remaining: int
    api_version: str


class CookieDetailResponse(BaseModel):
    """Respuesta de cookies relacionadas"""
    success: bool = True
    meta: CookieDetailMeta
    data: List[Dict[str, Any]]


class ValidationError(BaseModel):
    """Error de validación"""
    loc: List[Any]
    msg: str
    type: str
    input: Optional[Any] = None
    ctx: Optional[Dict[str, Any]] = None


class HTTPValidationError(BaseModel):
    """Error HTTP de validación"""
    detail: List[ValidationError]


# ========== Parámetros de Búsqueda ==========

class SearchParams(BaseModel):
    """Parámetros para búsqueda por dominio"""
    q: str = Field(..., min_length=3, max_length=253, description="Dominio a buscar")
    match_mode: str = Field(default="family", pattern="^(exact|family|fuzzy)$")
    sort: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=50, ge=1, description="Máximo de resultados (sin límite máximo)")
    offset: int = Field(default=0, ge=0)
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    
    @field_validator('q')
    @classmethod
    def validate_q(cls, v):
        if len(v) < 3:
            raise ValueError('Query debe tener al menos 3 caracteres')
        if len(v) > 253:
            raise ValueError('Query no puede exceder 253 caracteres')
        return v
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        # Sin límite máximo - el usuario puede solicitar cualquier cantidad
        return v


class UsernameSearchParams(BaseModel):
    """Parámetros para búsqueda por usuario"""
    q: str = Field(..., min_length=3, max_length=254, description="Usuario a buscar")
    sort: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=50, ge=1, description="Máximo de resultados (sin límite máximo)")
    offset: int = Field(default=0, ge=0)
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")


class EmailSearchParams(BaseModel):
    """Parámetros para búsqueda por email"""
    q: str = Field(..., min_length=3, max_length=254, description="Email a buscar")
    sort: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=50, ge=1, description="Máximo de resultados (sin límite máximo)")
    offset: int = Field(default=0, ge=0)
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")


class CookieSearchParams(BaseModel):
    """Parámetros para búsqueda de cookies"""
    q: str = Field(..., min_length=3, max_length=253, description="Dominio a buscar")
    match_mode: str = Field(default="family", pattern="^(exact|family|fuzzy)$")
    sort: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=50, ge=1, description="Máximo de resultados (sin límite máximo)")
    offset: int = Field(default=0, ge=0)
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")


# ========== Info de API ==========

class APIInfo(BaseModel):
    """Información de la API Leaksyr"""
    title: str = "Leaksyr API"
    version: str = "2.0.0"
    description: str = "Developer API for Leaksyr platform"
    
    class Config:
        frozen = True
