"""
Skill de integração com Ollama (LLM local).
Permite que o agente raciocine sobre diagnósticos antes de propor ações.
"""
import json
import requests
from datetime import datetime


OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "mistral"  # troque por llama3, phi3, qwen2 etc.


class OllamaSkill:
    """
    Conecta o GenieAgent ao Ollama para raciocínio sobre problemas.
    O LLM analisa o diagnóstico e SUGERE ações — nunca executa diretamente.
    """

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_BASE):
        self.model = model
        self.base_url = base_url

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.ok
        except Exception:
            return False

    def available_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.ok:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def analyze(self, context: dict, question: str | None = None) -> str:
        """
        Envia o diagnóstico do servidor para o LLM e pede análise.
        Retorna texto com a análise — nunca executa ações.
        """
        if not self.is_available():
            return "[Ollama não disponível — instale com: curl -fsSL https://ollama.com/install.sh | sh]"

        q = question or "Analise o estado do servidor e liste problemas encontrados, em português."
        prompt = (
            f"Você é um agente de suporte do GenialHub (sistema de gestão Genial Care).\n"
            f"REGRA: você pode sugerir ações mas NUNCA as executa sem aprovação de Rodrigo.\n\n"
            f"Diagnóstico atual do servidor:\n{json.dumps(context, indent=2, ensure_ascii=False)}\n\n"
            f"Pergunta: {q}"
        )

        try:
            r = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            if r.ok:
                return r.json().get("response", "[sem resposta]")
            return f"[erro Ollama: {r.status_code}]"
        except requests.Timeout:
            return "[timeout — modelo pode estar carregando, tente novamente]"
        except Exception as e:
            return f"[erro: {e}]"

    def suggest_fix(self, alert: dict) -> str:
        """Pede ao LLM uma sugestão de correção para um alerta específico."""
        return self.analyze(
            context=alert,
            question=(
                f"O alerta é: {alert.get('mensagem', alert)}. "
                "Qual a causa mais provável e o que eu devo verificar primeiro? "
                "Liste passos de diagnóstico em ordem de prioridade."
            )
        )

    # Compatibilidade com interface Skill
    def before(self, ordem): pass
    def after(self, ordem, concluido): pass
    def on_error(self, error, ordem):
        print(f"[OllamaSkill] Analisando erro com LLM: {error}")
        análise = self.analyze({"error": str(error)}, "O que pode ter causado este erro?")
        print(f"[LLM] {análise}")
    def on_success(self, ordem): pass
