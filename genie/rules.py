"""
Regras de segurança do Genie.
Todo agente deve respeitar estas regras sem exceção.
"""

RULES = {
    # Ações sempre permitidas (leitura pura)
    "allow_read": [
        "check_disk",
        "check_memory",
        "check_cpu",
        "check_processes",
        "read_logs",
        "docker_status",
        "docker_logs",
        "app_health",
        "db_query_readonly",
        "list_services",
    ],
    # Ações que exigem confirmação de Rodrigo antes de executar
    "require_confirm": [
        "restart_service",
        "restart_container",
        "run_migration",
        "update_env",
        "delete_file",
        "kill_process",
        "run_sql_write",
        "push_notification",
        "deploy",
    ],
    # Ações completamente proibidas (nunca executar automaticamente)
    "never_auto": [
        "drop_table",
        "delete_database",
        "remove_user",
        "reset_password",
        "revoke_token",
        "format_disk",
    ],
}


def can_auto_execute(action: str) -> bool:
    return action in RULES["allow_read"]


def requires_confirm(action: str) -> bool:
    return action in RULES["require_confirm"]


def is_forbidden(action: str) -> bool:
    return action in RULES["never_auto"]


def check_permission(action: str) -> str:
    """
    Retorna: 'allow', 'confirm', ou 'deny'
    """
    if is_forbidden(action):
        return "deny"
    if requires_confirm(action):
        return "confirm"
    if can_auto_execute(action):
        return "allow"
    # Por padrão, ação desconhecida exige confirmação
    return "confirm"
