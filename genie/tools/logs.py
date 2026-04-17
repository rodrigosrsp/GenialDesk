"""
Ferramentas de leitura de logs — SOMENTE LEITURA.
"""
import os
import subprocess
import re
from datetime import datetime


LOG_PATHS = {
    "nginx": "/var/log/nginx/error.log",
    "api": "/srv/GenialHub/logs/api.log",
    "system": "/var/log/syslog",
    "docker": None,  # via docker logs
}


class LogTools:
    """Leitura e análise de logs do sistema."""

    @staticmethod
    def tail(path: str, lines: int = 100) -> list[str]:
        if not os.path.exists(path):
            return [f"[arquivo não encontrado: {path}]"]
        result = subprocess.run(["tail", "-n", str(lines), path], capture_output=True, text=True)
        return result.stdout.splitlines()

    @staticmethod
    def grep(path: str, pattern: str, lines: int = 50) -> list[str]:
        if not os.path.exists(path):
            return [f"[arquivo não encontrado: {path}]"]
        result = subprocess.run(
            ["grep", "-i", "-m", str(lines), pattern, path],
            capture_output=True, text=True
        )
        return result.stdout.splitlines()

    @staticmethod
    def docker_logs(container: str, lines: int = 100, grep: str | None = None) -> list[str]:
        cmd = ["docker", "logs", "--tail", str(lines), container]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = (result.stdout + result.stderr).splitlines()
        if grep:
            pattern = re.compile(grep, re.IGNORECASE)
            output = [l for l in output if pattern.search(l)]
        return output

    @staticmethod
    def errors_summary() -> dict:
        """Resumo de erros recentes em todos os logs conhecidos."""
        summary = {"timestamp": datetime.now().isoformat(), "sources": {}}
        for name, path in LOG_PATHS.items():
            if path is None:
                continue
            errors = LogTools.grep(path, "error|exception|critical|fatal", lines=20)
            summary["sources"][name] = {
                "path": path,
                "recent_errors": errors[:10],
                "count": len(errors),
            }
        return summary

    @staticmethod
    def nginx_errors(lines: int = 50) -> list[str]:
        return LogTools.tail(LOG_PATHS["nginx"], lines)

    @staticmethod
    def genialhub_logs(lines: int = 100) -> list[str]:
        containers = ["api", "genialhub_api", "genialhub-api-1"]
        for c in containers:
            logs = LogTools.docker_logs(c, lines)
            if logs and "[erro" not in logs[0]:
                return logs
        return [f"[container api não encontrado]"]
