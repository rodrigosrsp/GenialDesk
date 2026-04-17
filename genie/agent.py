class GenieAgent:
    """
    Agente que força a execução contínua de tarefas até a conclusão total.
    """
    def __init__(self):
        self.skills = []
 
    def use_skill(self, skill):
        self.skills.append(skill)

    def execute(self, ordem):
        for skill in self.skills:
            skill.before(ordem)
        concluido = False
        while not concluido:
            try:
                concluido = ordem()
            except Exception as e:
                for skill in self.skills:
                    skill.on_error(e, ordem)
            for skill in self.skills:
                skill.after(ordem, concluido)
        for skill in self.skills:
            skill.on_success(ordem)


def run_with_genie(ordem):
    """
    Função helper para executar uma ordem usando GenieAgent e ForceContinueUntilDone.
    Basta passar uma função que retorna True quando concluída.
    """
    from .skills import ForceContinueUntilDone
    agent = GenieAgent()
    agent.use_skill(ForceContinueUntilDone())
    agent.execute(ordem)
