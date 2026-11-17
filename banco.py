
import os
import sqlite3
import sys


def pasta_do_programa():
    """Descobre a pasta onde o programa está."""

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))


CAMINHO_BANCO = os.path.join(
    pasta_do_programa(),
    "funciona_mente.db"
)


def conectar():
    """Estabelece uma conexão com o banco SQLite."""

    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def criar_tabelas():
    """Cria as tabelas necessárias para o sistema."""

    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                tipo TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                terapeuta_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                telefone TEXT,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (terapeuta_id)
                    REFERENCES usuarios(id)
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                terapeuta_id INTEGER NOT NULL,
                paciente_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                anotacoes TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (terapeuta_id)
                    REFERENCES usuarios(id),

                FOREIGN KEY (paciente_id)
                    REFERENCES pacientes(id)
            )
        """)

        conexao.execute("""
            CREATE TRIGGER IF NOT EXISTS validar_atendimento_insert
            BEFORE INSERT ON atendimentos
            FOR EACH ROW
            WHEN NOT EXISTS (
                SELECT 1
                FROM pacientes
                WHERE id = NEW.paciente_id
                AND terapeuta_id = NEW.terapeuta_id
            )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Paciente não pertence a este terapeuta.'
                );
            END
        """)

        conexao.execute("""
            CREATE TRIGGER IF NOT EXISTS validar_atendimento_update
            BEFORE UPDATE ON atendimentos
            FOR EACH ROW
            WHEN NOT EXISTS (
                SELECT 1
                FROM pacientes
                WHERE id = NEW.paciente_id
                AND terapeuta_id = NEW.terapeuta_id
            )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Paciente não pertence a este terapeuta.'
                );
            END
        """)

with conectar() as conexao:
    colunas = conexao.execute(
        "PRAGMA table_info(pacientes)"
    ).fetchall()

    nomes_colunas = [
        coluna["name"] for coluna in colunas
    ]

    if "usuario_id" not in nomes_colunas:
        conexao.execute(
            """
            ALTER TABLE pacientes
            ADD COLUMN usuario_id INTEGER
            REFERENCES usuarios(id)
            """
        )

    conexao.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_pacientes_usuario_id
        ON pacientes(usuario_id)
        """
    )

def criar_conta(usuario):
    """Armazena uma nova conta no banco de dados."""

    import seguranca

    nome, email, senha, tipo = usuario

    senha_hash = seguranca.gerar_hash(senha)

    try:
        with conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, tipo)
                VALUES (?, ?, ?, ?)
                """,
                (nome.strip(), email.strip().lower(), senha_hash, tipo)
            )

        return True

    except sqlite3.IntegrityError:
        raise ValueError("Este e-mail já está cadastrado.")


def buscar_usuario_por_email(email):
    """Busca um usuário pelo endereço de e-mail."""

    with conectar() as conexao:
        usuario = conexao.execute(
            """
            SELECT id, nome, email, senha_hash, tipo
            FROM usuarios
            WHERE email = ?
            """,
            (email.strip().lower(),)
        ).fetchone()

    return usuario

def cadastrar_paciente(terapeuta_id, nome, email, telefone):
    """Cadastra um paciente vinculado a um terapeuta."""

    with conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO pacientes (terapeuta_id, nome, email, telefone)
            VALUES (?, ?, ?, ?)
            """,
            (terapeuta_id, nome.strip(), email.strip(), telefone.strip())
        )

    return True

def vincular_conta_paciente(terapeuta_id, paciente_id, email):
    """Vincula uma conta de paciente ao cadastro correspondente."""

    with conectar() as conexao:
        usuario = conexao.execute(
            """
            SELECT id
            FROM usuarios
            WHERE email = ?
            AND tipo = 'paciente'
            """,
            (email.strip().lower(),)
        ).fetchone()

        if usuario is None:
            return False

        cursor = conexao.execute(
            """
            UPDATE pacientes
            SET usuario_id = ?
            WHERE id = ?
            AND terapeuta_id = ?
            AND LOWER(email) = ?
            AND usuario_id IS NULL
            """,
            (
                usuario["id"],
                paciente_id,
                terapeuta_id,
                email.strip().lower()
            )
        )

        return cursor.rowcount > 0

def listar_pacientes(terapeuta_id):
    """Lista somente os pacientes de determinado terapeuta."""

    with conectar() as conexao:
        pacientes = conexao.execute(
            """
            SELECT id, nome, email, telefone, criado_em, usuario_id
            FROM pacientes
            WHERE terapeuta_id = ?
            ORDER BY nome
            """,
            (terapeuta_id,)
        ).fetchall()

    return pacientes

def editar_paciente(terapeuta_id, paciente_id, nome, email, telefone):
    """Edita um paciente pertencente ao terapeuta."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE pacientes
            SET nome = ?, email = ?, telefone = ?
            WHERE id = ? AND terapeuta_id = ?
            """,
            (
                nome.strip(),
                email.strip(),
                telefone.strip(),
                paciente_id,
                terapeuta_id
            )
        )

    return cursor.rowcount > 0

def excluir_paciente(terapeuta_id, paciente_id):
    """Exclui um paciente pertencente ao terapeuta."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM pacientes
            WHERE id = ? AND terapeuta_id = ?
            """,
            (paciente_id, terapeuta_id)
        )

    return cursor.rowcount > 0

def registrar_atendimento(
    terapeuta_id,
    paciente_id,
    data,
    anotacoes
):
    """Registra um atendimento de um paciente."""

    with conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO atendimentos (
                terapeuta_id,
                paciente_id,
                data,
                anotacoes
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                terapeuta_id,
                paciente_id,
                data,
                anotacoes
            )
        )

    return True

def listar_atendimentos(terapeuta_id, paciente_id):
    """Lista os atendimentos de um paciente."""

    with conectar() as conexao:
        atendimentos = conexao.execute(
            """
            SELECT id, data, anotacoes, criado_em
            FROM atendimentos
            WHERE terapeuta_id = ?
            AND paciente_id = ?
            ORDER BY data DESC
            """,
            (terapeuta_id, paciente_id)
        ).fetchall()

    return atendimentos

def editar_atendimento(
    terapeuta_id,
    atendimento_id,
    data,
    anotacoes
):
    """Edita um atendimento do terapeuta."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE atendimentos
            SET data = ?, anotacoes = ?
            WHERE id = ? AND terapeuta_id = ?
            """,
            (
                data,
                anotacoes,
                atendimento_id,
                terapeuta_id
            )
        )

    return cursor.rowcount > 0

def excluir_atendimento(terapeuta_id, atendimento_id):
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            DELETE FROM atendimentos
            WHERE id = ? AND terapeuta_id = ?
            """,
            (atendimento_id, terapeuta_id)
        )

        return cursor.rowcount > 0