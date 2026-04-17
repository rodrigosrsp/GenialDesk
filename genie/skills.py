class ForceContinueUntilDone:
    """
    Skill que garante a execução até a conclusão da ordem.
    """
    def before(self, ordem):
        print("[GenieSkill] Iniciando execução forçada...")
 
    def after(self, ordem, concluido):
        if not concluido:
            print("[GenieSkill] Ordem ainda não concluída. Reexecutando...")
        else:
            print("[GenieSkill] Ordem concluída!")

    def on_error(self, error, ordem):
        print(f"[GenieSkill] Erro detectado: {error}. Tentando novamente...")

    def on_success(self, ordem):
        print("[GenieSkill] Execução finalizada com sucesso.")
