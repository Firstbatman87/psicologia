
import bcrypt


def gerar_hash(senha):
    """Gera um hash bcrypt para a senha."""

    senha_bytes = senha.encode("utf-8")

    if len(senha_bytes) > 72:
        raise ValueError("A senha ultrapassa o limite de 72 bytes.")

    hash_bytes = bcrypt.hashpw(
        senha_bytes,
        bcrypt.gensalt(rounds=12)
    )

    return hash_bytes.decode("utf-8")


def verificar_senha(senha, senha_hash):
    """Verifica se a senha corresponde ao hash armazenado."""

    senha_bytes = senha.encode("utf-8")
    hash_bytes = senha_hash.encode("utf-8")

    if len(senha_bytes) > 72:
        return False

    return bcrypt.checkpw(senha_bytes, hash_bytes)
