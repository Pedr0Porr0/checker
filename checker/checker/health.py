"""Health Check Monitor para Leaksyr API"""

import time
from typing import Dict, Any, Optional
from .api_client import LeaksyrClient


class HealthChecker:
    """Monitor de salud de la API Leaksyr"""
    
    def __init__(self, api_key: Optional[str] = None, interval: int = 30):
        """
        Inicializa el monitor de salud
        
        Args:
            api_key: Clave API
            interval: Intervalo de verificación en segundos
        """
        self.client = LeaksyrClient(api_key)
        self.interval = interval
        self.status_history = []
    
    def check(self) -> Dict[str, Any]:
        """Verifica el estado actual de la API"""
        try:
            result = self.client.health_check()
            status = {
                "timestamp": time.time(),
                "healthy": True,
                "data": result
            }
        except Exception as e:
            status = {
                "timestamp": time.time(),
                "healthy": False,
                "error": str(e)
            }
        
        self.status_history.append(status)
        return status
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los chequeos"""
        if not self.status_history:
            return {}
        
        total = len(self.status_history)
        healthy = sum(1 for s in self.status_history if s.get("healthy", False))
        
        return {
            "total_checks": total,
            "healthy_count": healthy,
            "failed_count": total - healthy,
            "uptime_percentage": (healthy / total * 100) if total > 0 else 0,
            "latest_status": self.status_history[-1]
        }


if __name__ == "__main__":
    checker = HealthChecker()
    status = checker.check()
    print(f"Status: {status}")
    print(f"Stats: {checker.get_stats()}")
