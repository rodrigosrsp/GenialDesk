"""
CLI do Genie — ponto de entrada para diagnóstico e monitoramento.
Uso: python -m genie.cli [comando]
"""
import sys
import json
from .tools.server import ServerTools
from .tools.docker import DockerTools
from .tools.app import AppTools
from .tools.logs import LogTools
from .skills.monitoring import MonitoringSkill
from .skills.propose import ProposeAndConfirm
from .skills.ollama import OllamaSkill


def cmd_status():
    report = {
        **ServerTools.full_report(),
        "docker": DockerTools.full_report(),
        "app": AppTools.full_report(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_monitor(interval: int = 60):
    proposer = ProposeAndConfirm(auto_approve=False)
    skill = MonitoringSkill(interval_seconds=interval, proposer=proposer)
    skill.run_loop()


def cmd_analyze():
    ollama = OllamaSkill()
    if not ollama.is_available():
        print("Ollama não disponível. Instale: curl -fsSL https://ollama.com/install.sh | sh")
        print(f"Modelos disponíveis após instalar: mistral, llama3, phi3")
        sys.exit(1)
    monitor = MonitoringSkill()
    report = monitor.collect()
    print("[Genie] Analisando diagnóstico com LLM...")
    análise = ollama.analyze(report)
    print("\n─── Análise do LLM ───")
    print(análise)


def cmd_logs(container: str = "api", lines: int = 100):
    logs = LogTools.docker_logs(container, lines)
    for line in logs:
        print(line)


COMMANDS = {
    "status": cmd_status,
    "monitor": cmd_monitor,
    "analyze": cmd_analyze,
    "logs": cmd_logs,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = COMMANDS.get(cmd)
    if fn:
        fn()
    else:
        print(f"Comandos disponíveis: {', '.join(COMMANDS)}")
        sys.exit(1)
