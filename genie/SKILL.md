# Genie Agent Skill: force_continue_until_done
 
Esta skill garante que o agente continue tentando executar a ordem até que ela seja concluída com sucesso, mesmo diante de falhas temporárias.

## Métodos
- `before(ordem)`: Executado antes de cada tentativa.
- `after(ordem, concluido)`: Executado após cada tentativa, verifica se deve continuar.
- `on_error(error, ordem)`: Executado em caso de erro, força nova tentativa.
- `on_success(ordem)`: Executado ao final, quando a ordem for concluída.

## Exemplo de uso
```python
from genie.agent import GenieAgent
from genie.skills import ForceContinueUntilDone

def minha_ordem():
    # Retorne True se concluído, False caso contrário
    ...

agent = GenieAgent()
agent.use_skill(ForceContinueUntilDone())
agent.execute(minha_ordem)
```
