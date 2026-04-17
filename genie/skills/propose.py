"""
Skill de proposta com confirmação.
REGRA: O agente NUNCA executa ações destrutivas ou de escrita sem aprovação de Rodrigo.

Fluxo:
  1. Agent detecta problema
  2. Propõe ação com justificativa
  3. Aguarda confirmação (console ou arquivo de aprovação)
  4. Só executa após 'sim' explícito
"""
import os
import json
import time
from datetime import datetime
from ..rules import check_permission


PENDING_DIR = os.environ.get("GENIE_PENDING_DIR", "/srv/genie-pending")


class ProposeAndConfirm:
    """
    Skill que intercepta ações que requerem confirmação.
    Salva proposta em arquivo e aguarda aprovação.
    """

    def __init__(self, auto_approve: bool = False, timeout_seconds: int = 300):
        self.auto_approve = auto_approve  # NUNCA True em produção
        self.timeout = timeout_seconds
        os.makedirs(PENDING_DIR, exist_ok=True)

    def propose(self, action: str, justificativa: str, comando: str | None = None) -> dict:
        """
        Registra uma proposta e aguarda confirmação de Rodrigo.
        Retorna {'aprovado': True/False, 'id': str}
        """
        permission = check_permission(action)

        if permission == "deny":
            print(f"[Genie] ❌ Ação '{action}' PROIBIDA — não será executada.")
            return {"aprovado": False, "motivo": "ação proibida pelas regras"}

        if permission == "allow":
            return {"aprovado": True, "motivo": "ação de leitura — pré-autorizada"}

        # permission == "confirm" — precisa de aprovação
        proposta_id = f"proposta-{int(time.time())}"
        proposta = {
            "id": proposta_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "justificativa": justificativa,
            "comando": comando,
            "status": "aguardando",
        }

        path = os.path.join(PENDING_DIR, f"{proposta_id}.json")
        with open(path, "w") as f:
            json.dump(proposta, f, indent=2, ensure_ascii=False)

        print(f"\n[Genie] ⚠️  PROPOSTA DE AÇÃO — AGUARDANDO APROVAÇÃO DE RODRIGO")
        print(f"  Ação:         {action}")
        print(f"  Justificativa:{justificativa}")
        if comando:
            print(f"  Comando:      {comando}")
        print(f"  Proposta ID:  {proposta_id}")
        print(f"  Arquivo:      {path}")
        print(f"  Para aprovar: echo 'sim' > {path.replace('.json', '.approve')}")
        print(f"  Para rejeitar:echo 'nao' > {path.replace('.json', '.approve')}\n")

        if self.auto_approve:
            print("[Genie] ⚠️  AUTO_APPROVE ativo — aprovando automaticamente (NÃO usar em produção!)")
            return {"aprovado": True, "id": proposta_id}

        return self._aguardar_resposta(proposta_id, path)

    def _aguardar_resposta(self, proposta_id: str, path: str) -> dict:
        approve_file = path.replace(".json", ".approve")
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if os.path.exists(approve_file):
                with open(approve_file) as f:
                    resposta = f.read().strip().lower()
                os.remove(approve_file)
                aprovado = resposta in ("sim", "s", "yes", "y", "1")
                # Atualiza proposta com resultado
                with open(path) as f:
                    p = json.load(f)
                p["status"] = "aprovado" if aprovado else "rejeitado"
                p["resposta_em"] = datetime.now().isoformat()
                with open(path, "w") as f:
                    json.dump(p, f, indent=2, ensure_ascii=False)
                print(f"[Genie] {'✅ Aprovado' if aprovado else '❌ Rejeitado'} pelo operador.")
                return {"aprovado": aprovado, "id": proposta_id}
            time.sleep(5)

        print(f"[Genie] ⏰ Timeout — proposta {proposta_id} expirou sem resposta.")
        return {"aprovado": False, "id": proposta_id, "motivo": "timeout"}

    # Compatibilidade com interface Skill do GenieAgent
    def before(self, ordem): pass
    def after(self, ordem, concluido): pass
    def on_error(self, error, ordem): pass
    def on_success(self, ordem): pass
