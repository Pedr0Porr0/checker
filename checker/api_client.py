"""Leaksyr API 2.0.0 Client"""

import os
import requests
from typing import Optional, Dict, Any, Literal, Union
from urllib.parse import urlencode
from dotenv import load_dotenv
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError

from .models import (
    SearchResponse,
    CookieDetailResponse,
    SearchParams,
    UsernameSearchParams,
    EmailSearchParams,
    CookieSearchParams,
    HTTPValidationError,
)

load_dotenv()


class LeaksyrClient:
    """Client para la API de Leaksyr 2.0.0"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Leaksyr
        
        Args:
            api_key: Clave API de Leaksyr. Si no se proporciona, se lee de .env
        """
        self.api_key = api_key or os.getenv("LEAKSYR_API_KEY")
        self.base_url = os.getenv("LEAKSYR_BASE_URL", "https://leaksyr.com/api")
        self.session = requests.Session()
        
        # Configurar headers de autenticación con X-API-Key
        # Según el panel de Leaksyr: X-API-Key (no Bearer token)
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Checker/1.0.0 (Leaksyr API Client)"
        })
        
        if not self.api_key:
            raise ValueError("LEAKSYR_API_KEY no configurada. Configura en .env")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Realiza una petición a la API con manejo robusto de errores
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Punto final de la API
            params: Parámetros query
            **kwargs: Argumentos adicionales para requests
            
        Returns:
            Respuesta JSON de la API
            
        Raises:
            HTTPError: Error HTTP de la API
            Timeout: Timeout en la conexión
            ConnectionError: Error de conexión
            ValueError: Error de validación (422)
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method, 
                url, 
                params=params,
                timeout=30,  # 30 segundos timeout
                **kwargs
            )
            
            # Manejar errores específicos
            if response.status_code == 422:
                # Error de validación
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', [])
                    if not error_detail and 'message' in error_data:
                        raise ValueError(f"Validation Error: {error_data['message']}")
                    if not error_detail:
                        raise ValueError(f"Validation Error: {error_data}")
                    error_msgs = [f"{err.get('loc', 'unknown')}: {err.get('msg', 'error')}" 
                                 for err in error_detail]
                    raise ValueError(f"Validation Error: {'; '.join(error_msgs)}")
                except ValueError:
                    raise
                except Exception:
                    raise ValueError(f"Validation Error: {response.text}")
            
            if response.status_code == 401:
                raise ValueError("Autenticación fallida. Verifica tu API Key")
            
            if response.status_code == 403:
                raise ValueError("Acceso denegado. Tu API Key no tiene permiso para este recurso")
            
            response.raise_for_status()
            return response.json()
            
        except Timeout as e:
            raise Timeout(f"Timeout al conectar con {url}: {e}")
        except ConnectionError as e:
            raise ConnectionError(f"Error de conexión con {url}: {e}")
        except HTTPError as e:
            if response.status_code >= 500:
                raise HTTPError(f"Error del servidor (HTTP {response.status_code}): {e}")
            raise
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en petición a {url}: {e}")
    
    def health_check(self) -> str:
        """
        Verifica el estado de la API
        
        Returns:
            "OK" si la API está activa
            
        Raises:
            Exception: Si hay error de conexión o la API no responde
        """
        return self._make_request("GET", "/health")
    
    # ========== BÚSQUEDA POR DOMINIO ==========
    
    def search_domain(
        self,
        domain: str,
        match_mode: Literal["family", "exact", "fuzzy"] = "family",
        sort: Literal["asc", "desc"] = "desc",
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> SearchResponse:
        """
        Busca logs filtrados por dominio
        
        Args:
            domain: Dominio a buscar (e.g. 'google.com')
            match_mode: family (subdomios), exact (host único), fuzzy (substring)
            sort: Orden de resultados (asc/desc)
            limit: Máximo de resultados (sin límite, default 50)
            offset: Pagination offset
            start_date: Filtrar desde (YYYY-MM-DD)
            end_date: Filtrar hasta (YYYY-MM-DD)
            idempotency_key: Header de idempotencia
            
        Returns:
            SearchResponse con resultados
            
        Raises:
            ValueError: Si la validación falla
            HTTPError: Si hay error en la API
        """
        # Validar parámetros con Pydantic
        search_params = SearchParams(
            q=domain,
            match_mode=match_mode,
            sort=sort,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        
        params = search_params.model_dump(exclude_none=True)
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        response_data = self._make_request(
            "GET",
            "/v2/search",
            params=params,
            headers=headers
        )
        
        return SearchResponse(**response_data)
    
    # ========== BÚSQUEDA POR USUARIO ==========
    
    def search_username(
        self,
        username: str,
        sort: Literal["asc", "desc"] = "desc",
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> SearchResponse:
        """
        Busca logs por nombre de usuario exacto
        
        Args:
            username: Usuario a buscar (búsqueda exacta)
            sort: Orden de resultados
            limit: Máximo de resultados (sin límite, default 50)
            offset: Pagination offset
            start_date: Filtrar desde (YYYY-MM-DD)
            end_date: Filtrar hasta (YYYY-MM-DD)
            idempotency_key: Header de idempotencia
            
        Returns:
            SearchResponse con resultados
            
        Raises:
            ValueError: Si la validación falla
        """
        # Validar parámetros con Pydantic
        search_params = UsernameSearchParams(
            q=username,
            sort=sort,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        
        params = search_params.model_dump(exclude_none=True)
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        response_data = self._make_request(
            "GET",
            "/v2/search/username",
            params=params,
            headers=headers
        )
        
        return SearchResponse(**response_data)
    
    # ========== BÚSQUEDA POR EMAIL ==========
    
    def search_email(
        self,
        email: str,
        sort: Literal["asc", "desc"] = "desc",
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> SearchResponse:
        """
        Busca logs por email exacto
        
        Args:
            email: Email a buscar (búsqueda exacta)
            sort: Orden de resultados
            limit: Máximo de resultados (sin límite, default 50)
            offset: Pagination offset
            start_date: Filtrar desde (YYYY-MM-DD)
            end_date: Filtrar hasta (YYYY-MM-DD)
            idempotency_key: Header de idempotencia
            
        Returns:
            SearchResponse con resultados
            
        Raises:
            ValueError: Si la validación falla
        """
        # Validar parámetros con Pydantic
        search_params = EmailSearchParams(
            q=email,
            sort=sort,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        
        params = search_params.model_dump(exclude_none=True)
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        response_data = self._make_request(
            "GET",
            "/v2/search/email",
            params=params,
            headers=headers
        )
        
        return SearchResponse(**response_data)
    
    # ========== BÚSQUEDA DE COOKIES (Business-tier) ==========
    
    def search_cookies(
        self,
        domain: str,
        match_mode: Literal["family", "exact", "fuzzy"] = "family",
        sort: Literal["asc", "desc"] = "desc",
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> SearchResponse:
        """
        Busca cookies por dominio (Business-tier API keys only)
        
        Args:
            domain: Dominio a buscar
            match_mode: family, exact o fuzzy
            sort: Orden de resultados
            limit: Máximo de resultados (sin límite, default 50)
            offset: Pagination offset
            start_date: Filtrar desde (YYYY-MM-DD)
            end_date: Filtrar hasta (YYYY-MM-DD)
            idempotency_key: Header de idempotencia
            
        Returns:
            SearchResponse con resultados de cookies
            
        Raises:
            ValueError: Si es acceso denegado (no Business-tier)
        """
        # Validar parámetros con Pydantic
        search_params = CookieSearchParams(
            q=domain,
            match_mode=match_mode,
            sort=sort,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )
        
        params = search_params.model_dump(exclude_none=True)
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        response_data = self._make_request(
            "GET",
            "/v2/search/cookies",
            params=params,
            headers=headers
        )
        
        return SearchResponse(**response_data)
    
    # ========== COOKIES RELACIONADAS (Business-tier) ==========
    
    def get_related_cookies(
        self,
        cookie_id: str,
        idempotency_key: Optional[str] = None,
    ) -> CookieDetailResponse:
        """
        Obtiene todas las cookies relacionadas para un cookie_id
        (mismo source_id y eTLD+1 family - reconstruye sesión completa)
        
        Args:
            cookie_id: ID de la cookie (de /v2/search/cookies/)
            idempotency_key: Header de idempotencia
            
        Returns:
            CookieDetailResponse con cookies relacionadas
            
        Raises:
            ValueError: Si la cookie_id no existe o acceso denegado
        """
        if not cookie_id or not isinstance(cookie_id, str) or len(cookie_id) == 0:
            raise ValueError("cookie_id debe ser un string no vacío")
        
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        response_data = self._make_request(
            "GET",
            f"/v2/search/cookies/{cookie_id}/related",
            headers=headers
        )
        
        return CookieDetailResponse(**response_data)
    
    def close(self):
        """Cierra la sesión"""
        self.session.close()


if __name__ == "__main__":
    # Prueba de conexión
    try:
        client = LeaksyrClient()
        health = client.health_check()
        print(f"✓ API Health: {health}")
    except Exception as e:
        print(f"✗ Error: {e}")
