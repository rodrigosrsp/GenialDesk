"""
Skill de monitoramento periódico do servidor e da aplicação.
Coleta métricas e gera alertas — NUNCA age autonomamente.
"""
import time
from datetime import datetime
from ..tools.server import ServerTools
from ..tools.docker import DockerTools
from ..tools.app import AppTools


class MonitoringSkill:
    """
    Executa diagnóstico completo e reporta alertas.
    Ao detectar problema, propõe ação mas aguarda confirmação.
    """

    def __init__(self, interval_seconds: int = 60, proposer=None):
        self.interval = interval_seconds
        self.proposer = proposer  # instância de ProposeAndConfirm
        self._alerts = []

    def collect(self) -> dict:
        report = {
            "timestamp": datetime.now().isoformat(),
            "server": ServerTools.full_report(),
            "docker": DockerTools.full_report(),
            "app": AppTools.full_report(),
            "alerts": [],
        }
        self._check_alerts(report)
        report["alerts"] = self._alerts.copy()
        self._alerts.clear()
        return report

    def _check_alerts(self, report: dict):
        # Disco cheio
        disk = report["server"].get("disk", {})
        if disk.get("alert"):
            self._add_alert(
                "disk_high",
                f"Disco {disk['path']} com {disk['used_pct']}% usado ({disk['free_gb']} GB livres)",
                severity="warning" if disk["used_pct"] < 90 else "critical",
            )

        # Memória alta
        mem = report["server"].get("memory", {})
        if mem.get("alert"):
            self._add_alert(
                "memory_high",
                f"Memória com {mem['used_pct']}% uso ({mem['available_gb']} GB disponíveis)",
                severity="warning",
            )

        # CPU alta
        cpu = report["server"].get("cpu", {})
        if cpu.get("alert"):
            self._add_alert("cpu_high", f"CPU a {cpu['used_pct']}%", severity="warning")

        # API offline
        api = report["app"].get("api_health", {})
        if api.get("status") not in (200, 201):
            self._add_alert(
                "api_down",
                f"GenialHub API não respondendo (status: {api.get('status')})",
                severity="critical",
            )

    def _add_alert(self, tipo: str, mensagem: str, severity: str = "warning"):
        alert = {
            "tipo": tipo,
            "mensagem": mensagem,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        }
        self._alerts.append(alert)
        icon = "🔴" if severity == "critical" else "⚠️"
        print(f"[Genie Monitor] {icon} {mensagem}")

        # Se há um proposer configurado e o alerta é crítico, propõe ação
        if self.proposer and severity == "critical":
            self._propor_acao(tipo, mensagem)

    def _propor_acao(self, tipo: str, mensagem: str):
        acoes = {
            "api_down": ("restart_container", "API está fora do ar — propondo restart do container"),
            "disk_high": ("check_disk", "Disco cheio — revisar logs e arquivos grandes"),
        }
        if tipo in acoes:
            action, justificativa = acoes[tipo]
            self.proposer.propose(action, justificativa)

    def run_once(self) -> dict:
        return self.collect()

    def run_loop(self):
        print(f"[Genie Monitor] Iniciando monitoramento a cada {self.interval}s...")
        while True:
            try:
                report = self.collect()
                if not report["alerts"]:
                    print(f"[Genie Monitor] ✅ {report['timestamp']} — tudo OK")
            except Exception as e:
                print(f"[Genie Monitor] Erro ao coletar métricas: {e}")
            time.sleep(self.interval)

    # Compatibilidade com interface Skill
    def before(self, ordem): pass
    def after(self, ordem, concluido): pass
    def on_error(self, error, ordem): print(f"[MonitoringSkill] erro: {error}")
    def on_success(self, ordem): pass
