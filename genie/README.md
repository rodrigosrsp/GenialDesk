# Genie Agent
 
Este agente é responsável por garantir que qualquer tarefa recebida seja executada até sua conclusão total, sem interrupções ou desistências prematuras. Ele força a continuidade do fluxo de trabalho até que a ordem expressa seja totalmente cumprida.

## Objetivo
- Forçar a execução contínua de tarefas até a conclusão.
- Não permitir que o agente pare ou peça confirmação antes de terminar a ordem.
- Ideal para automações críticas, pipelines e execuções que não podem ser interrompidas.

## Como usar
- Importe e utilize o Genie Agent em fluxos onde a conclusão total é mandatória.
- Combine com skills que reforcem a persistência e monitoramento do progresso.

---

# Genie Skill: force_continue_until_done

Esta skill deve ser usada em conjunto com o Genie Agent para garantir que o agente continue executando até que a tarefa seja concluída.

## Descrição
- Monitora o status da tarefa.
- Reexecuta etapas falhas automaticamente.
- Só retorna sucesso quando a ordem for totalmente cumprida.

## Exemplo de uso
```python
from genie.agent import GenieAgent
from genie.skills import force_continue_until_done

agent = GenieAgent()
agent.use_skill(force_continue_until_done)
agent.execute(ordem)
```
