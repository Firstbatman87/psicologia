import os
import sqlite3
import sys
import utilidades
from datetime import datetime, timedelta

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

        colunas = conexao.execute(
                "PRAGMA table_info(pacientes)"
            ).fetchall()
        
        nomes_colunas = [coluna["name"] for coluna in colunas]
        
        if "ativo" not in nomes_colunas:
                conexao.execute("""
                ALTER TABLE pacientes
                ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1
            """)

        conexao.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_pacientes_terapeuta_email
            ON pacientes (
            terapeuta_id,
            LOWER(TRIM(email))
            )
            WHERE email IS NOT NULL
            AND TRIM(email) <> ''
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
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                terapeuta_id INTEGER NOT NULL,
                paciente_id INTEGER NOT NULL,
                data_hora TEXT NOT NULL,
                duracao INTEGER NOT NULL DEFAULT 50,
                status TEXT NOT NULL DEFAULT 'agendado',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (terapeuta_id)
                    REFERENCES usuarios(id),

                FOREIGN KEY (paciente_id)
                    REFERENCES pacientes(id),

                CHECK (duracao > 0),

                CHECK (
                    status IN (
                        'agendado',
                        'realizado',
                        'cancelado'
                    )
                )
            )
        """)

        conexao.execute("""
            DROP TRIGGER IF EXISTS validar_atendimento_insert
        """)

        conexao.execute("""
            CREATE TRIGGER validar_atendimento_insert
            BEFORE INSERT ON atendimentos
            FOR EACH ROW
            WHEN NOT EXISTS (
                SELECT 1
                FROM pacientes
                WHERE id = NEW.paciente_id
                AND terapeuta_id = NEW.terapeuta_id
                AND ativo = 1
            )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Paciente não pertence a este terapeuta ou está inativo.'
                );
            END
        """)

        conexao.execute("""
            DROP TRIGGER IF EXISTS validar_atendimento_update
        """)

        conexao.execute("""
            CREATE TRIGGER validar_atendimento_update
            BEFORE UPDATE ON atendimentos
            FOR EACH ROW
            WHEN NOT EXISTS (
                SELECT 1
                FROM pacientes
                WHERE id = NEW.paciente_id
                AND terapeuta_id = NEW.terapeuta_id
                AND ativo = 1
            )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Paciente não pertence a este terapeuta ou está inativo.'
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

    try:
        with conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO pacientes (
                    terapeuta_id,
                    nome,
                    email,
                    telefone
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    terapeuta_id,
                    nome.strip(),
                    email.strip().lower(),
                    telefone.strip()
                )
            )

        return True

    except sqlite3.IntegrityError as erro:
        if "idx_pacientes_terapeuta_email" in str(erro):
            raise ValueError(
                "Este terapeuta já possui um paciente com esse e-mail."
            )

        raise

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
            AND ativo = 1
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
    """Inativa um paciente pertencente ao terapeuta."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE pacientes
            SET ativo = 0
            WHERE id = ?
            AND terapeuta_id = ?
            AND ativo = 1
            """,
            (paciente_id, terapeuta_id)
        )

    return cursor.rowcount > 0

def reativar_paciente(terapeuta_id, paciente_id):
    """Reativa um paciente pertencente ao terapeuta."""

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE pacientes
            SET ativo = 1
            WHERE id = ?
            AND terapeuta_id = ?
            AND ativo = 0
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
    """Registra um atendimento de um paciente ativo."""

    with conectar() as conexao:

        paciente = conexao.execute(
            """
            SELECT id
            FROM pacientes
            WHERE id = ?
            AND terapeuta_id = ?
            AND ativo = 1
            """,
            (paciente_id, terapeuta_id)
        ).fetchone()

        if paciente is None:
            raise ValueError(
                "Paciente não encontrado ou está inativo."
            )

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

def listar_pacientes_inativos(terapeuta_id):
    """Lista os pacientes inativos de um terapeuta."""

    with conectar() as conexao:
        pacientes = conexao.execute(
            """
            SELECT id, nome, email, telefone, criado_em
            FROM pacientes
            WHERE terapeuta_id = ?
            AND ativo = 0
            ORDER BY nome
            """,
            (terapeuta_id,)
        ).fetchall()

    return pacientes

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

def listar_atendimentos_paciente(usuario_id):
    """Lista as datas dos atendimentos vinculados à conta do paciente."""
    with conectar() as conexao:
        atendimentos = conexao.execute(
            """
            SELECT
                atendimentos.id,
                atendimentos.data
            FROM atendimentos
            INNER JOIN pacientes
                ON atendimentos.paciente_id = pacientes.id
            WHERE pacientes.usuario_id = ?
            AND pacientes.ativo = 1
            ORDER BY atendimentos.data DESC
            """,
            (usuario_id,)
        ).fetchall()

        return atendimentos

def buscar_dados_paciente(usuario_id):
    """Busca os dados cadastrais do próprio paciente."""

    with conectar() as conexao:
        paciente = conexao.execute(
            """
            SELECT nome, email, telefone, criado_em
            FROM pacientes
            WHERE usuario_id = ?
            AND ativo = 1
            """,
            (usuario_id,)
        ).fetchone()

    return paciente

def editar_meus_dados_paciente(usuario_id, nome, email, telefone):
    """Permite ao paciente editar seus próprios dados cadastrais."""

    with conectar() as conexao:

        # Localiza o cadastro vinculado à conta.
        paciente = conexao.execute(
            """
            SELECT id, terapeuta_id
            FROM pacientes
            WHERE usuario_id = ?
            AND ativo = 1
            """,
            (usuario_id,)
        ).fetchone()

        if paciente is None:
            return False

        # Verifica se o e-mail pertence a outra conta.
        conta_existente = conexao.execute(
            """
            SELECT id
            FROM usuarios
            WHERE usuario_id = ?
            AND ativo = 1
            AND id != ?
            """,
            (email.strip(), usuario_id)
        ).fetchone()

        if conta_existente:
            raise ValueError(
                "Este e-mail já pertence a outra conta."
            )

        # Verifica se outro paciente do mesmo terapeuta
        # já utiliza esse e-mail.
        paciente_existente = conexao.execute(
            """
            SELECT id
            FROM pacientes
            WHERE terapeuta_id = ?
            AND LOWER(TRIM(email)) = LOWER(TRIM(?))
            AND id != ?
            """,
            (
                paciente["terapeuta_id"],
                email,
                paciente["id"]
            )
        ).fetchone()

        if paciente_existente:
            raise ValueError(
                "Outro paciente deste terapeuta já utiliza esse e-mail."
            )

        cursor = conexao.execute(
            """
            UPDATE pacientes
            SET nome = ?, email = ?, telefone = ?
            WHERE usuario_id = ?
            """,
            (nome.strip(), email.strip().lower(), telefone.strip(), usuario_id)
        )

    return cursor.rowcount > 0

def paciente_esta_ativo(usuario_id):
    """Verifica se a conta possui um cadastro de paciente ativo."""

    with conectar() as conexao:
        paciente = conexao.execute(
            """
            SELECT id
            FROM pacientes
            WHERE usuario_id = ?
            AND ativo = 1
            """,
            (usuario_id,)
        ).fetchone()

    return paciente is not None 

def verificar_conflito_agendamento(
    terapeuta_id,
    data_hora,
    duracao,
    agendamento_id=None
):
    """Verifica se existe outro agendamento no mesmo horário."""

    inicio_novo = datetime.strptime(
        data_hora, "%Y-%m-%d %H:%M"
    )

    fim_novo = inicio_novo + timedelta(minutes=duracao)

    with conectar() as conexao:
        agendamentos = conexao.execute(
            """
            SELECT data_hora, duracao
            FROM agendamentos
            WHERE terapeuta_id = ?
            AND status != 'cancelado'
            AND (? IS NULL OR id != ?)
            """,
            (terapeuta_id, agendamento_id, agendamento_id)
        ).fetchall()

    for agendamento in agendamentos:
        inicio_existente = datetime.strptime(
            agendamento["data_hora"],
            "%Y-%m-%d %H:%M"
        )

        fim_existente = inicio_existente + timedelta(
            minutes=agendamento["duracao"]
        )

        if inicio_novo < fim_existente and fim_novo > inicio_existente:
            return True

    return False

def cadastrar_agendamento(
    terapeuta_id,
    paciente_id,
    data_hora,
    duracao=50
):
    """Cadastra um agendamento para um paciente."""

    utilidades.verificar_agendamento(data_hora, duracao)
    if verificar_conflito_agendamento(
        terapeuta_id,
        data_hora,
        duracao
    ):
        raise ValueError(
            "Já existe um agendamento nesse horário."
        )
    with conectar() as conexao:
        paciente = conexao.execute(
            """
            SELECT id
            FROM pacientes
            WHERE id = ?
            AND terapeuta_id = ?
            AND ativo = 1
            """,
            (paciente_id, terapeuta_id)
        ).fetchone()

        if paciente is None:
            raise ValueError(
                "Paciente não encontrado ou está inativo."
            )

        conexao.execute(
            """
            INSERT INTO agendamentos (
                terapeuta_id,
                paciente_id,
                data_hora,
                duracao
            )
            VALUES (?, ?, ?, ?)
            """,
            (terapeuta_id, paciente_id, data_hora, duracao)
        )

def listar_agendamentos(terapeuta_id):
    """Lista os agendamentos de um terapeuta."""

    with conectar() as conexao:
        agendamentos = conexao.execute(
            """
            SELECT
                agendamentos.id,
                agendamentos.data_hora,
                agendamentos.duracao,
                agendamentos.status,
                pacientes.nome AS paciente_nome

            FROM agendamentos

            INNER JOIN pacientes
                ON agendamentos.paciente_id = pacientes.id

            WHERE agendamentos.terapeuta_id = ?

            ORDER BY agendamentos.data_hora
            """,
            (terapeuta_id,)
        ).fetchall()

    return agendamentos

def atualizar_status_agendamento(
    terapeuta_id,
    agendamento_id,
    novo_status
):
    """Atualiza o status de um agendamento."""

    status_permitidos = (
        "agendado",
        "realizado",
        "cancelado"
    )

    if novo_status not in status_permitidos:
        raise ValueError("Status inválido.")

    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE agendamentos
            SET status = ?
            WHERE id = ?
            AND terapeuta_id = ?
            """,
            (novo_status, agendamento_id, terapeuta_id)
        )

    return cursor.rowcount > 0

def editar_agendamento(
    terapeuta_id,
    agendamento_id,
    data_hora,
    duracao
):
    """Edita a data e a duração de um agendamento."""

    utilidades.verificar_agendamento(data_hora, duracao)

    with conectar() as conexao:
        agendamento = conexao.execute(
            """
            SELECT id
            FROM agendamentos
            WHERE id = ?
            AND terapeuta_id = ?
            AND status = 'agendado'
            """,
            (agendamento_id, terapeuta_id)
        ).fetchone()

        if agendamento is None:
            raise ValueError(
                "Agendamento não encontrado ou não pode ser editado."
            )

        if verificar_conflito_agendamento(
            terapeuta_id,
            data_hora,
            duracao,
            agendamento_id
        ):
            raise ValueError(
                "Já existe um agendamento nesse horário."
            )

        conexao.execute(
            """
            UPDATE agendamentos
            SET data_hora = ?,
                duracao = ?
            WHERE id = ?
            AND terapeuta_id = ?
            """,
            (
                data_hora,
                duracao,
                agendamento_id,
                terapeuta_id
            )
        )