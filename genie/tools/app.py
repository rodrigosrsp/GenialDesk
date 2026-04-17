"""
Ferramentas de diagnóstico do GenialHub — SOMENTE LEITURA.
"""
import os
import subprocess
import requests
from datetime import datetime


GENIALHUB_API = os.environ.get("GENIALHUB_API", "http://localhost:3000")
AGENT_SECRET = os.environ.get("AGENT_SECRET", "genial-agent-secret")

HEADERS = {"Authorization": f"Bearer {AGENT_SECRET}"}


def _get(path: str, timeout: int = 5) -> dict:
    try:
        r = requests.get(f"{GENIALHUB_API}{path}", headers=HEADERS, timeout=timeout)
        return {"status": r.status_code, "body": r.json() if r.ok else r.text}
    except requests.ConnectionError:
        return {"status": None, "error": "API não acessível"}
    except Exception as e:
        return {"status": None, "error": str(e)}


class AppTools:
    """Diagnóstico da aplicação GenialHub."""

    @staticmethod
    def health() -> dict:
        return _get("/health")

    @staticmethod
    def stats() -> dict:
        return _get("/api/agents/stats")

    @staticmethod
    def device_count() -> dict:
        return _get("/api/devices?limit=1")

    @staticmethod
    def recent_logs(lines: int = 100) -> list[str]:
        log_paths = [
            "/srv/GenialHub/logs/api.log",
            "/var/log/genialhub.log",
        ]
        for path in log_paths:
            if os.path.exists(path):
                result = subprocess.run(
                    ["tail", "-n", str(lines), path],
                    capture_output=True, text=True
                )
                return result.stdout.splitlines()
        return ["[nenhum arquivo de log encontrado]"]

    @staticmethod
    def db_size() -> dict:
        """Consulta tamanho do banco via psql (read-only)."""
        cmd = [
            "docker", "exec", "postgres",
            "psql", "-U", "postgres", "-d", "genialhub", "-c",
            "SELECT pg_size_pretty(pg_database_size('genialhub')) AS size;"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "output": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
            "ok": result.returncode == 0,
        }

    @staticmethod
    def full_report() -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "api_health": AppTools.health(),
            "db_size": AppTools.db_size(),
        }
