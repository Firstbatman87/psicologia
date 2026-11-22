import banco
import utilidades
import seguranca
import permissoes

def menu():
    print("\n=== FUNCIONA MENTE ===")
    print("1 - Entrar na conta")
    print("2 - Criar conta")
    print("0 - Sair")
    return input("Escolha uma opção: ")


def criar_conta():
    print("\n=== CRIAR CONTA ===")

    nome = input("Digite seu nome: ")
    email = input("Digite seu e-mail: ")
    senha = input("Digite sua senha: ")
    tipo = input("Tipo de conta (terapeuta/paciente): ").strip().lower()

    usuario = (nome, email, senha, tipo)

    try:
        utilidades.verificar_criacao(usuario)
        banco.criar_conta(usuario)
        print("\nConta criada com sucesso!")

    except ValueError as erro:
        print(f"\nErro: {erro}")


def entrar_conta():
    print("\n=== ENTRAR NA CONTA ===")

    email = input("E-mail: ").strip().lower()
    senha = input("Senha: ")

    usuario = banco.buscar_usuario_por_email(email)

    if usuario is None:
        print("\nE-mail ou senha incorretos.")
        return None

    senha_correta = seguranca.verificar_senha(
        senha,
        usuario["senha_hash"]
    )

    if usuario["tipo"] == "paciente":
        if not banco.paciente_esta_ativo(usuario["id"]):
            print("\nEsta conta não possui um cadastro de paciente ativo.")
            return None

    if not senha_correta:
        print("\nE-mail ou senha incorretos.")
        return None

    print(f"\nBem-vindo(a), {usuario['nome']}!")

    sessao = {
        "autenticado": True,
        "usuario_id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"]
    }

    return sessao

def cadastrar_paciente(sessao):
    """Cadastra um paciente para o terapeuta autenticado."""

    try:
        permissoes.exigir_permissao(
            sessao, "cadastrar_pacientes"
        )

        print("\n=== CADASTRAR PACIENTE ===")

        nome = input("Nome do paciente: ").strip()
        email = input("E-mail do paciente: ").strip().lower()
        telefone = input("Telefone do paciente: ").strip()

        if not nome:
            print("\nO nome não pode ficar vazio.")
            return

        if email:
            utilidades.verificar_dados_paciente(nome, email)

        banco.cadastrar_paciente(
            sessao["usuario_id"],
            nome,
            email,
            telefone
        )

        print("\nPaciente cadastrado com sucesso!")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

    except ValueError as erro:
        print(f"\nErro: {erro}")

def consultar_pacientes(sessao):
    """Consulta os pacientes do terapeuta autenticado."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        print("\n=== MEUS PACIENTES ===")

        if not pacientes:
            print("Nenhum paciente cadastrado.")
            return

        for paciente in pacientes:
            print(f"\nID: {paciente['id']}")
            print(f"Nome: {paciente['nome']}")
            print(f"E-mail: {paciente['email'] or 'Não informado'}")
            print(f"Telefone: {paciente['telefone'] or 'Não informado'}")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def editar_paciente(sessao):
    """Permite editar um paciente do terapeuta autenticado."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        print("\n=== EDITAR PACIENTE ===")

        try:
            paciente_id = int(input("ID do paciente: "))
        except ValueError:
            print("\nDigite um ID válido.")
            return

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        paciente = next(
            (p for p in pacientes if p["id"] == paciente_id),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        print(f"\nEditando: {paciente['nome']}")

        nome = input("Novo nome: ")
        email = input("Novo e-mail: ")
        telefone = input("Novo telefone: ")

        if not nome.strip():
            print("\nO nome não pode ficar vazio.")
            return

        atualizado = banco.editar_paciente(
            sessao["usuario_id"],
            paciente_id,
            nome,
            email,
            telefone
        )

        if atualizado:
            print("\nPaciente atualizado com sucesso!")
        else:
            print("\nNão foi possível atualizar o paciente.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def excluir_paciente(sessao):
    """Exclui um paciente do terapeuta autenticado."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        print("\n=== EXCLUIR PACIENTE ===")

        try:
            paciente_id = int(input("ID do paciente: "))
        except ValueError:
            print("\nDigite um ID válido.")
            return

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        paciente = next(
            (p for p in pacientes if p["id"] == paciente_id),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        print(f"\nPaciente: {paciente['nome']}")

        confirmacao = input(
            "Tem certeza que deseja excluir? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("\nExclusão cancelada.")
            return

        excluido = banco.excluir_paciente(
            sessao["usuario_id"],
            paciente_id
        )

        if excluido:
            print("\nPaciente excluído com sucesso!")
        else:
            print("\nNão foi possível excluir o paciente.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def reativar_paciente(sessao):
    try:
        permissoes.exigir_permissao(
            sessao,
            "cadastrar_pacientes"
        )

        print("\n=== REATIVAR PACIENTE ===")

        pacientes = banco.listar_pacientes_inativos(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nNão existem pacientes inativos.")
            return

        for paciente in pacientes:
            print(f'{paciente["id"]} - {paciente["nome"]}')

        paciente_id = int(input("\nID do paciente: "))

        if banco.reativar_paciente(
            sessao["usuario_id"],
            paciente_id
        ):
            print("\nPaciente reativado com sucesso!")
        else:
            print("\nNão foi possível reativar esse paciente.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")
    except ValueError:
        print("\nDigite um ID válido.")

def registrar_atendimento(sessao):
    """Registra um atendimento para um paciente."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê ainda não possui pacientes cadastrados.")
            return

        print("\n=== SELECIONAR PACIENTE ===")

        for paciente in pacientes:
            print(f"{paciente['id']} - {paciente['nome']}")

        try:
            paciente_id = int(input("\nID do paciente: "))
        except ValueError:
            print("\nDigite um ID válido.")
            return

        paciente = next(
            (p for p in pacientes if p["id"] == paciente_id),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        print(f"\n=== ATENDIMENTO DE {paciente['nome'].upper()} ===")

        data = input("Data do atendimento (AAAA-MM-DD): ")
        anotacoes = input("Anotações do atendimento: ")

        if not data.strip() or not anotacoes.strip():
            print("\nA data e as anotações são obrigatórias.")
            return

        banco.registrar_atendimento(
            sessao["usuario_id"],
            paciente_id,
            data,
            anotacoes
        )

        print("\nAtendimento registrado com sucesso!")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def consultar_atendimentos(sessao):
    """Consulta o histórico de atendimentos de um paciente."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê ainda não possui pacientes cadastrados.")
            return

        print("\n=== SELECIONAR PACIENTE ===")

        for paciente in pacientes:
            print(f"{paciente['id']} - {paciente['nome']}")

        try:
            paciente_id = int(input("\nID do paciente: "))
        except ValueError:
            print("\nDigite um ID válido.")
            return

        paciente = next(
            (p for p in pacientes if p["id"] == paciente_id),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        atendimentos = banco.listar_atendimentos(
            sessao["usuario_id"],
            paciente_id
        )

        print(f"\n=== HISTÓRICO DE {paciente['nome'].upper()} ===")

        if not atendimentos:
            print("Nenhum atendimento registrado.")
            return

        for atendimento in atendimentos:
            print(f"\nID: {atendimento['id']}")
            print(f"Data: {atendimento['data']}")
            print(f"Anotações: {atendimento['anotacoes']}")
            print("-" * 40)

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def editar_atendimento(sessao):
    """Edita um atendimento existente."""

    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê não possui pacientes cadastrados.")
            return

        print("\n=== SELECIONAR PACIENTE ===")

        for paciente in pacientes:
            print(f"{paciente['id']} - {paciente['nome']}")

        try:
            paciente_id = int(input("\nID do paciente: "))
        except ValueError:
            print("\nDigite um ID válido.")
            return

        paciente = next(
            (p for p in pacientes if p["id"] == paciente_id),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        atendimentos = banco.listar_atendimentos(
            sessao["usuario_id"],
            paciente_id
        )

        if not atendimentos:
            print("\nEsse paciente não possui atendimentos.")
            return

        print("\n=== SELECIONAR ATENDIMENTO ===")

        for atendimento in atendimentos:
            print(
                f"ID: {atendimento['id']} | "
                f"Data: {atendimento['data']}"
            )

        try:
            atendimento_id = int(
            input("\nID do atendimento: ")
            )
        except ValueError:
            print("\nDigite um ID válido.")
            return

        atendimento = next(
            (
            a for a in atendimentos
            if a["id"] == atendimento_id
            ),
            None
        )

        if atendimento is None:
            print("\nAtendimento não encontrado.")
            return

        print("\n=== EDITAR ATENDIMENTO ===")
        print(f"Data atual: {atendimento['data']}")
        print(f"Anotações atuais: {atendimento['anotacoes']}")

        data = input("\nNova data (AAAA-MM-DD): ")
        anotacoes = input("Novas anotações: ")

        if not data.strip() or not anotacoes.strip():
            print("\nOs campos não podem ficar vazios.")
            return

        atualizado = banco.editar_atendimento(
            sessao["usuario_id"],
            atendimento_id,
            data,
            anotacoes
        )

        if atualizado:
            print("\nAtendimento atualizado com sucesso!")
        else:
            print("\nNão foi possível atualizar o atendimento.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def excluir_atendimento(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê não possui pacientes cadastrados.")
            return

        print("\n=== EXCLUIR ATENDIMENTO ===")

        for paciente in pacientes:
            print(f"ID: {paciente['id']} | Nome: {paciente['nome']}")

        paciente_id = input("\nID do paciente: ")

        if not paciente_id.isdigit():
            print("\nID inválido.")
            return

        paciente_id = int(paciente_id)

        paciente_encontrado = any(
            paciente["id"] == paciente_id
            for paciente in pacientes
        )

        if not paciente_encontrado:
            print("\nPaciente não encontrado.")
            return

        atendimentos = banco.listar_atendimentos(
            sessao["usuario_id"], paciente_id
        )

        if not atendimentos:
            print("\nEsse paciente não possui atendimentos.")
            return

        for atendimento in atendimentos:
            print(
                f"\nID: {atendimento['id']}"
                f"\nData: {atendimento['data']}"
                f"\nAnotações: {atendimento['anotacoes']}"
            )

        atendimento_id = input("\nID do atendimento que deseja excluir: ")

        if not atendimento_id.isdigit():
            print("\nID inválido.")
            return

        atendimento_id = int(atendimento_id)

        atendimento_encontrado = any(
            atendimento["id"] == atendimento_id
            for atendimento in atendimentos
        )

        if not atendimento_encontrado:
            print("\nAtendimento não encontrado.")
            return

        confirmacao = input(
            "\nTem certeza de que deseja excluir este atendimento? (s/n): "
        ).strip().lower()

        if confirmacao != "s":
            print("\nExclusão cancelada.")
            return

        excluido = banco.excluir_atendimento(
            sessao["usuario_id"], atendimento_id
        )

        if excluido:
            print("\nAtendimento excluído com sucesso!")
        else:
            print("\nNão foi possível excluir o atendimento.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def vincular_paciente(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "cadastrar_pacientes"
        )

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê não possui pacientes cadastrados.")
            return

        print("\n=== VINCULAR CONTA DE PACIENTE ===")

        for paciente in pacientes:
            status = (
                "Conta vinculada"
                if paciente["usuario_id"] is not None
                else "Sem conta vinculada"
            )

            print(
                f"\nID: {paciente['id']}"
                f"\nNome: {paciente['nome']}"
                f"\nE-mail: {paciente['email'] or 'Não informado'}"
                f"\nStatus: {status}"
            )

        paciente_id = input("\nID do paciente: ")

        if not paciente_id.isdigit():
            print("\nID inválido.")
            return

        paciente_id = int(paciente_id)

        paciente = next(
            (
                p for p in pacientes
                if p["id"] == paciente_id
            ),
            None
        )

        if paciente is None:
            print("\nPaciente não encontrado.")
            return

        if paciente["usuario_id"] is not None:
            print("\nEsse paciente já possui uma conta vinculada.")
            return

        if not paciente["email"]:
            print("\nEsse paciente não possui e-mail cadastrado.")
            return

        email = input(
            "\nDigite o e-mail da conta do paciente: "
        ).strip().lower()

        if email != paciente["email"].strip().lower():
            print("\nO e-mail não corresponde ao cadastro.")
            return

        vinculado = banco.vincular_conta_paciente(
            sessao["usuario_id"],
            paciente_id,
            email
        )

        if vinculado:
            print("\nConta vinculada com sucesso!")
        else:
            print("\nNão foi possível realizar o vínculo.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def consultar_proprios_atendimentos(sessao):
    try:
        permissoes.exigir_permissao(
            sessao,
            "consultar_proprios_atendimentos"
        )

        atendimentos = banco.listar_atendimentos_paciente(
            sessao["usuario_id"]
        )

        if not atendimentos:
            print("\nVocê não possui atendimentos registrados.")
            return

        print("\n=== MEUS ATENDIMENTOS ===")

        for atendimento in atendimentos:
            print(f"\nID: {atendimento['id']}")
            print(f"Data: {atendimento['data']}")

    except PermissionError as erro:
        print(erro)

def consultar_meus_dados_paciente(sessao):
    try:
        permissoes.exigir_permissao(
            sessao,
            "consultar_perfil"
        )

        if sessao["tipo"] != "paciente":
            raise PermissionError(
                "Esta função é exclusiva para pacientes."
            )

        paciente = banco.buscar_dados_paciente(
            sessao["usuario_id"]
        )

        if paciente is None:
            print("\nNenhum cadastro de paciente foi vinculado à sua conta.")
            return

        print("\n=== MEUS DADOS CADASTRAIS ===")
        print(f"Nome: {paciente['nome']}")
        print(f"E-mail: {paciente['email']}")
        print(f"Telefone: {paciente['telefone']}")

    except PermissionError as erro:
        print(erro)

def editar_meus_dados_paciente(sessao):
    try:
        permissoes.exigir_permissao(
            sessao,
            "consultar_perfil"
        )

        if sessao["tipo"] != "paciente":
            raise PermissionError(
                "Esta função é exclusiva para pacientes."
            )

        paciente = banco.buscar_dados_paciente(
            sessao["usuario_id"]
        )

        if paciente is None:
            print("\nCadastro de paciente não encontrado.")
            return

        print("\n=== EDITAR MEUS DADOS ===")
        print("Pressione Enter para manter o valor atual.")

        nome = input(
            f"Nome [{paciente['nome']}]: "
        ).strip() or paciente["nome"]

        email = input(
            f"E-mail [{paciente['email']}]: "
        ).strip().lower() or paciente["email"]

        telefone = input(
            f"Telefone [{paciente['telefone']}]: "
        ).strip() or paciente["telefone"]

        utilidades.verificar_dados_paciente(nome, email)

        atualizado = banco.editar_meus_dados_paciente(
            sessao["usuario_id"],
            nome,
            email,
            telefone
        )

        if atualizado:
            print("\nDados atualizados com sucesso!")
        else:
            print("\nNão foi possível atualizar os dados.")

    except PermissionError as erro:
        print(erro)

    except ValueError as erro:
        print(f"\nErro: {erro}")

def consultar_agendamentos(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        print("\n=== MINHA AGENDA ===")

        agendamentos = banco.listar_agendamentos(
            sessao["usuario_id"]
        )

        if not agendamentos:
            print("\nNão existem agendamentos cadastrados.")
            return

        for agendamento in agendamentos:
            print(f"\nID: {agendamento['id']}")
            print(f"Paciente: {agendamento['paciente_nome']}")
            print(f"Data e horário: {agendamento['data_hora']}")
            print(f"Duração: {agendamento['duracao']} minutos")
            print(f"Status: {agendamento['status']}")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

def cadastrar_agendamento(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "cadastrar_pacientes"
        )

        print("\n=== CADASTRAR AGENDAMENTO ===")

        pacientes = banco.listar_pacientes(
            sessao["usuario_id"]
        )

        if not pacientes:
            print("\nVocê não possui pacientes ativos.")
            return

        print("\n=== PACIENTES ===")

        for paciente in pacientes:
            print(f"{paciente['id']} - {paciente['nome']}")

        paciente_id = int(input("\nID do paciente: "))

        data_hora = input(
            "Data e horário (AAAA-MM-DD HH:MM): "
        ).strip()

        duracao = input(
            "Duração em minutos (pressione Enter para 50): "
        ).strip()

        duracao = 50 if not duracao else int(duracao)

        utilidades.verificar_agendamento(
            data_hora, duracao
        )

        banco.cadastrar_agendamento(
            sessao["usuario_id"],
            paciente_id,
            data_hora,
            duracao
        )

        print("\nAgendamento cadastrado com sucesso!")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

    except ValueError as erro:
        print(f"\nErro: {erro}")

def atualizar_status_agendamento(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        print("\n=== ATUALIZAR AGENDAMENTO ===")

        agendamentos = banco.listar_agendamentos(
            sessao["usuario_id"]
        )

        if not agendamentos:
            print("\nNão existem agendamentos cadastrados.")
            return

        for agendamento in agendamentos:
            print(
                f"\nID: {agendamento['id']} "
                f"- {agendamento['paciente_nome']}"
            )
            print(f"Data: {agendamento['data_hora']}")
            print(f"Status: {agendamento['status']}")

        agendamento_id = int(
            input("\nID do agendamento: ")
        )

        print("\n1 - Agendado")
        print("2 - Realizado")
        print("3 - Cancelado")

        opcao = input("\nNovo status: ")

        status = {
            "1": "agendado",
            "2": "realizado",
            "3": "cancelado"
        }

        if opcao not in status:
            print("\nOpção inválida.")
            return

        atualizado = banco.atualizar_status_agendamento(
            sessao["usuario_id"],
            agendamento_id,
            status[opcao]
        )

        if atualizado:
            print("\nStatus atualizado com sucesso!")
        else:
            print("\nAgendamento não encontrado.")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

    except ValueError:
        print("\nDigite um ID válido.")
        
def editar_agendamento(sessao):
    try:
        permissoes.exigir_permissao(
            sessao, "consultar_pacientes"
        )

        print("\n=== EDITAR AGENDAMENTO ===")

        agendamentos = banco.listar_agendamentos(
            sessao["usuario_id"]
        )

        agendamentos = [
            agendamento
            for agendamento in agendamentos
            if agendamento["status"] == "agendado"
        ]

        if not agendamentos:
            print("\nNão existem agendamentos disponíveis para edição.")
            return

        for agendamento in agendamentos:
            print(
                f"\nID: {agendamento['id']} "
                f"- {agendamento['paciente_nome']}"
            )
            print(f"Data: {agendamento['data_hora']}")
            print(f"Duração: {agendamento['duracao']} minutos")

        agendamento_id = int(
            input("\nID do agendamento: ")
        )

        data_hora = input(
            "Nova data e horário (AAAA-MM-DD HH:MM): "
        ).strip()

        duracao = int(
            input("Nova duração em minutos: ")
        )

        banco.editar_agendamento(
            sessao["usuario_id"],
            agendamento_id,
            data_hora,
            duracao
        )

        print("\nAgendamento atualizado com sucesso!")

    except PermissionError as erro:
        print(f"\nAcesso negado: {erro}")

    except ValueError as erro:
        print(f"\nErro: {erro}")

def menu_usuario(sessao):
    while True:
        print("\n=== ÁREA DO USUÁRIO ===")
        print(f"Usuário: {sessao['nome']}")
        print(f"Tipo: {sessao['tipo']}")

        print("\n1 - Consultar meus dados")

        if permissoes.verificar_permissao(
            sessao, "consultar_proprios_atendimentos"
        ):
            print("2 - Consultar meus atendimentos")

        if sessao["tipo"] == "paciente":
            print("3 - Editar meus dados")

        if permissoes.verificar_permissao(
            sessao, "cadastrar_pacientes"
        ):
            print("2 - Cadastrar pacientes")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("3 - Consultar meus pacientes")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("4 - Editar paciente")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("5 - Excluir paciente")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("6 - Registrar atendimento")
            print("7 - Consultar atendimentos")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("8 - Editar atendimento")

        if permissoes.verificar_permissao(
            sessao,  "consultar_pacientes"
        ):
            print("9 - Excluir atendimento")

        if permissoes.verificar_permissao(
            sessao, "cadastrar_pacientes"
        ):
            print("10 - Vincular conta de paciente")

        if permissoes.verificar_permissao(
            sessao, "cadastrar_pacientes"
        ):
            print("11 - Reativar paciente")

        if permissoes.verificar_permissao(
            sessao, "consultar_pacientes"
        ):
            print("12 - Consultar agenda")
            print("13 - Cadastrar agendamento")
            print("14 - Atualizar status de agendamento")
            print("15 - Editar agendamento")
            
        print("0 - Encerrar sessão")

        opcao = input("\nEscolha uma opção: ")

        if opcao == "1" and sessao["tipo"] == "paciente":
            consultar_meus_dados_paciente(sessao)

        elif opcao == "1" and sessao["tipo"] == "terapeuta":
            permissoes.exigir_permissao(
                sessao, "consultar_perfil"
            )

            print("\n=== MEUS DADOS ===")
            print(f"ID: {sessao['usuario_id']}")
            print(f"Nome: {sessao['nome']}")
            print(f"E-mail: {sessao['email']}")
            print(f"Tipo: {sessao['tipo']}")

        elif opcao == "2" and sessao["tipo"] == "paciente":
            consultar_proprios_atendimentos(sessao)

        elif opcao == "2" and sessao["tipo"] == "terapeuta":
            cadastrar_paciente(sessao)

        elif opcao == "3" and sessao["tipo"] == "terapeuta":
            consultar_pacientes(sessao)

        elif opcao == "4":
            editar_paciente(sessao)

        elif opcao == "5":
            excluir_paciente(sessao)

        elif opcao == "6":
            registrar_atendimento(sessao)

        elif opcao == "7":
            consultar_atendimentos(sessao)

        elif opcao == "8":
            editar_atendimento(sessao)

        elif opcao == "9":
            excluir_atendimento(sessao)

        elif opcao == "10":
            vincular_paciente(sessao)

        elif opcao == "3" and sessao["tipo"] == "paciente":
            editar_meus_dados_paciente(sessao)

        elif opcao == "11":
            reativar_paciente(sessao)

        elif opcao == "12":
            consultar_agendamentos(sessao)

        elif opcao == "13":
            cadastrar_agendamento(sessao)

        elif opcao == "14":
            atualizar_status_agendamento(sessao)

        elif opcao == "15":
            editar_agendamento(sessao)

        elif opcao == "0":
            print("\nSessão encerrada.")
            break

        else:
            print("\nOpção inválida.")

def executar():
    banco.criar_tabelas()

    while True:
        opcao = menu()

        if opcao == "1":
            sessao = entrar_conta()

            if sessao is not None:
                menu_usuario(sessao)

        elif opcao == "2":
            criar_conta()

        elif opcao == "0":
            print("\nEncerrando o programa.")
            break

        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    executar()