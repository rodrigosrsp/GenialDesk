"""
Ferramentas de diagnóstico Docker — SOMENTE LEITURA.
"""
import subprocess
import json
from datetime import datetime


def _run(cmd: list[str]) -> tuple[str, int]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


class DockerTools:
    """Monitoramento de containers Docker."""

    @staticmethod
    def list_containers(all: bool = True) -> list[dict]:
        args = ["docker", "ps", "--format", "{{json .}}"]
        if all:
            args.insert(2, "-a")
        out, code = _run(args)
        if code != 0:
            return [{"error": "docker não disponível ou sem permissão"}]
        containers = []
        for line in out.splitlines():
            if line.strip():
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return containers

    @staticmethod
    def container_logs(name: str, lines: int = 50) -> str:
        out, code = _run(["docker", "logs", "--tail", str(lines), name])
        return out if code == 0 else f"[erro ao ler logs: {code}]"

    @staticmethod
    def container_stats() -> list[dict]:
        out, code = _run(["docker", "stats", "--no-stream", "--format", "{{json .}}"])
        if code != 0:
            return [{"error": "não foi possível obter stats"}]
        stats = []
        for line in out.splitlines():
            if line.strip():
                try:
                    stats.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return stats

    @staticmethod
    def compose_status(project_dir: str) -> str:
        out, code = _run(["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "ps"])
        return out if code == 0 else f"[erro: {code}]"

    @staticmethod
    def genialhub_status() -> str:
        return DockerTools.compose_status("/srv/GenialHub")

    @staticmethod
    def full_report() -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "containers": DockerTools.list_containers(),
            "stats": DockerTools.container_stats(),
            "genialhub_compose": DockerTools.genialhub_status(),
        }
