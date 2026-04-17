"""
Ferramentas de diagnóstico do servidor — SOMENTE LEITURA.
Nunca modificam estado. Seguras para execução automática.
"""
import os
import shutil
import subprocess
import psutil
from datetime import datetime


class ServerTools:
    """Diagnóstico de hardware e sistema operacional."""

    @staticmethod
    def disk_usage(path: str = "/") -> dict:
        total, used, free = shutil.disk_usage(path)
        pct = (used / total) * 100
        return {
            "path": path,
            "total_gb": round(total / 1e9, 2),
            "used_gb": round(used / 1e9, 2),
            "free_gb": round(free / 1e9, 2),
            "used_pct": round(pct, 1),
            "alert": pct > 85,
        }

    @staticmethod
    def memory_usage() -> dict:
        m = psutil.virtual_memory()
        return {
            "total_gb": round(m.total / 1e9, 2),
            "used_gb": round(m.used / 1e9, 2),
            "available_gb": round(m.available / 1e9, 2),
            "used_pct": m.percent,
            "alert": m.percent > 85,
        }

    @staticmethod
    def cpu_usage(interval: float = 1.0) -> dict:
        pct = psutil.cpu_percent(interval=interval)
        return {
            "used_pct": pct,
            "cores": psutil.cpu_count(),
            "alert": pct > 85,
        }

    @staticmethod
    def top_processes(n: int = 10) -> list[dict]:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:n]

    @staticmethod
    def uptime() -> dict:
        boot = psutil.boot_time()
        delta = datetime.now().timestamp() - boot
        hours = int(delta // 3600)
        return {
            "uptime_hours": hours,
            "boot_time": datetime.fromtimestamp(boot).isoformat(),
        }

    @staticmethod
    def full_report() -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "disk": ServerTools.disk_usage("/"),
            "disk_srv": ServerTools.disk_usage("/srv"),
            "memory": ServerTools.memory_usage(),
            "cpu": ServerTools.cpu_usage(interval=0.5),
            "uptime": ServerTools.uptime(),
        }
