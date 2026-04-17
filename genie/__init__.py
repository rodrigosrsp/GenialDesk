"""
Genie — Framework de agentes Genial Care
Regra fundamental: nunca modificar dados sem confirmação de Rodrigo.
"""
from .agent import GenieAgent, run_with_genie
from .rules import RULES

__all__ = ['GenieAgent', 'run_with_genie', 'RULES']
