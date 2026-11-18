
import re


def verificar_criacao(usuario):
    """Valida os dados necessários para criar uma conta."""

    nome, email, senha, tipo = usuario

    if not nome.strip():
        raise ValueError("O nome não pode ficar vazio.")

    if not email.strip():
        raise ValueError("O e-mail não pode ficar vazio.")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        raise ValueError("Digite um e-mail válido.")

    if len(senha.encode("utf-8")) < 8:
        raise ValueError("A senha precisa ter pelo menos 8 bytes.")

    if len(senha.encode("utf-8")) > 72:
        raise ValueError("A senha ultrapassa o limite de 72 bytes.")

    tipos_permitidos = ("terapeuta", "paciente")

    if tipo not in tipos_permitidos:
        raise ValueError("Tipo de conta inválido.")

    return True

def verificar_dados_paciente(nome, email):
    """Valida os dados cadastrais do paciente."""

    if not nome.strip():
        raise ValueError("O nome não pode ficar vazio.")

    if not email.strip():
        raise ValueError("O e-mail não pode ficar vazio.")

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email.strip()
    ):
        raise ValueError("Digite um e-mail válido.")

    return True