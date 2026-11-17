def verificar_permissao(sessao, permissao):
    """Verifica se o usuário autenticado possui determinada permissão."""

    if not sessao or not sessao.get("autenticado"):
        return False

    tipo = sessao.get("tipo")

    permissoes = {
        "terapeuta": [
            "consultar_perfil",
            "cadastrar_pacientes",
            "consultar_pacientes"
        ],

        "paciente": [
            "consultar_perfil"
        ]
    }

    permissoes_usuario = permissoes.get(tipo, [])

    return permissao in permissoes_usuario


def exigir_permissao(sessao, permissao):
    """Impede a execução de operações não autorizadas."""

    if not verificar_permissao(sessao, permissao):
        raise PermissionError(
            "Você não possui autorização para executar esta operação."
        )
