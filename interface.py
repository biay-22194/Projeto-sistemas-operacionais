import customtkinter as ctk
from gantt import GraficoGantt
from CTkTable import CTkTable
from tkinter import filedialog
from pathlib import Path
from dataclasses import dataclass, field
from structs import TCB, RateMonotonic, EarliestDeadlineFirst
from utils import validar_configuracao
from simulator import Simulador

# Lista de estados válidos permitidos para as tarefas do sistema
ESTADOS_VALIDOS = ["Nova", "Pronta", "Executando", "Bloqueada", "Concluída"]

# ----------------------------------------------------------------------------------------------------------------------------------------------
# INTERFACE GRÁFICA E POP-UPS
# ----------------------------------------------------------------------------------------------------------------------------------------------
def mostrar_alerta_erro(parent_app, mensagem):
    """
    Exibe uma janela modal (pop-up) de erro para alertar o utilizador sobre alterações recusadas ou falhas de validação.
    Garante o foco na janela e evita problemas de renderização em ambientes Linux.
    """
    popup = ctk.CTkToplevel(parent_app)
    popup.title("Alteração Não Permitida")
    popup.geometry("450x180")
    
    # Configurações para garantir o comportamento modal correto
    popup.transient(parent_app)
    popup.wait_visibility()
    popup.grab_set() 
    popup.focus()

    # Rótulo de mensagem de erro com formatação destacada
    lbl_erro = ctk.CTkLabel(
        popup, 
        text=mensagem, 
        text_color="#FF5555", 
        wraplength=410, 
        font=("Arial", 12),
        justify="left"
    )
    lbl_erro.pack(pady=20, padx=15)

    # Botão de confirmação para fechar a janela modal
    btn_fechar = ctk.CTkButton(popup, text="Entendido", command=popup.destroy, width=110)
    btn_fechar.pack(pady=5)


def start_interface():
    """
    Função principal que inicializa a interface gráfica, constrói os formulários,
    associa os eventos aos botões e gere o ciclo de vida do simulador.
    """
    # Configuração global do tema visual da aplicação
    ctk.set_appearance_mode("dark")
    
    app = ctk.CTk()
    app.title("Simulador Visual de Sistema Operacional")
    app.geometry("1100x750")
    
    # 1. Valores Padrão do Sistema Operacional
    VALORES_PADRAO_SO = {
        "algoritmo": "RM",
        "quantum": 2,
        "cpus": 1
    }
    config_so = VALORES_PADRAO_SO.copy()

    # 2. INJEÇÃO DE TAREFAS PADRÃO (
    tcbs_do_sistema = [
        TCB(id="T1", cor="red", ingresso=0, duracao=3, periodo=10, prazo=10, lista_eventos=[]),
        TCB(id="T2", cor="blue", ingresso=2, duracao=2, periodo=6, prazo=6, lista_eventos=[])
    ]
    
    # Variáveis de controle do simulador e da interface gráfica
    simulador = None
    tabela_so_widget = None  
    tabela_tarefas_widget = None
    label_tick = None

    # -------------------------------------------------------------------------
    # RENDERIZAÇÃO DAS TABELAS INFORMATIVAS
    # -------------------------------------------------------------------------
    def atualizar_tabela_so():
        """Atualiza a tabela visual com os parâmetros atuais do SO (Algoritmo, Quantum, CPUs e Estado)."""
        nonlocal tabela_so_widget
        
        # Destrói o widget anterior para evitar sobreposição
        if tabela_so_widget is not None:
            tabela_so_widget.destroy()

        status_sim = f"Rodando (Tick {simulador.tempo_global})" if simulador else "Aguardando Início"
        dados_so = [
            ["Algoritmo", "Quantum", "Qtd. CPUs", "Estado do Simulador"],
            [
                config_so["algoritmo"].upper(),
                str(config_so["quantum"]),
                str(config_so["cpus"]),
                status_sim
            ]
        ]

        # Criação da nova tabela formatada
        tabela_so_widget = CTkTable(
            master=frame_tabela_so_container,
            values=dados_so,
            header_color="#1f538d",
            colors=["#2b2b2b", "#333333"]
        )
        tabela_so_widget.pack(expand=True, fill="both", padx=5, pady=5)

    def atualizar_tabela_tarefas():
        """Atualiza a tabela com o conjunto de tarefas e as suas respetivas características e estados."""
        nonlocal tabela_tarefas_widget
        
        if tabela_tarefas_widget is not None:
            tabela_tarefas_widget.destroy()

        dados_tarefas = [["ID", "Cor", "Ingresso", "Duração", "Período", "Prazo", "Estado Atual"]]
        
        # Preenche as linhas da tabela com os atributos de cada TCB
        for t in tcbs_do_sistema:
            estado_atual = getattr(t, 'estado', 'Nova')
            dados_tarefas.append([
                str(t.id),
                str(t.cor),
                str(t.ingresso),
                str(t.duracao),
                str(t.periodo),
                str(t.prazo),
                str(estado_atual)
            ])

        tabela_tarefas_widget = CTkTable(
            master=frame_tabela_tarefas_container, 
            values=dados_tarefas, 
            header_color="#1f538d",
            colors=["#2b2b2b", "#333333"]
        )
        tabela_tarefas_widget.pack(expand=True, fill="both", padx=5, pady=5)

    def carregar_simulador_inicial():
        """Instancia o objeto Simulador com as configurações atuais e as tarefas ativas."""
        nonlocal simulador
        if not tcbs_do_sistema:
            simulador = None
            return

        alg_nome = config_so["algoritmo"].upper()
        quantum_val = config_so["quantum"]
        cpus_val = config_so["cpus"]

        # Seleção da classe do algoritmo de escalonamento
        if alg_nome == "RM":
            escalonador = RateMonotonic(quantum=quantum_val)
        elif alg_nome == "EDF":
            escalonador = EarliestDeadlineFirst(quantum=quantum_val)
        else:
            raise ValueError("Algoritmo inválido.")

        # Inicialização do motor de simulação
        simulador = Simulador(
            tarefas=tcbs_do_sistema,
            algoritmo=escalonador,
            qtde_cpus=cpus_val
        )
        label_tick.configure(text="Tick atual: 0")

    # -------------------------------------------------------------------------
    # MODIFICAÇÕES ANTES E DURANTE A EXECUÇÃO COM VALIDAÇÃO SEMÂNTICA 
    # -------------------------------------------------------------------------
    def aplicar_config_so():
        """Aplica alterações de configuração do SO (Algoritmo, Quantum, CPUs) em tempo de execução."""
        try:
            novo_alg = combo_algoritmo.get().strip().upper()
            txt_quantum = entry_so_quantum.get().strip()
            txt_cpus = entry_so_cpus.get().strip()

            q_val = int(txt_quantum) if txt_quantum else config_so["quantum"]
            c_val = int(txt_cpus) if txt_cpus else config_so["cpus"]

            # Validações dos limites numéricos
            if q_val <= 0:
                mostrar_alerta_erro(app, "Modificação Recusada:\nO Quantum precisa ser um número maior que zero (>= 1).")
                return

            if c_val <= 0:
                mostrar_alerta_erro(app, "Modificação Recusada:\nO sistema necessita de pelo menos 1 CPU ativa para funcionar.")
                return

            config_so["algoritmo"] = novo_alg
            config_so["quantum"] = q_val
            config_so["cpus"] = c_val

            # Aplicação dinâmica no simulador ativo sem necessidade de reiniciar
            if simulador:
                simulador.qtde_cpus = c_val
                simulador.algoritmo.quantum = q_val
                if novo_alg == "RM":
                    simulador.algoritmo = RateMonotonic(quantum=q_val)
                else:
                    simulador.algoritmo = EarliestDeadlineFirst(quantum=q_val)
                simulador.algoritmo.preparar_tarefas(simulador.tarefas)

            atualizar_tabela_so()
            label_status.configure(text="Configurações do SO atualizadas com sucesso!", text_color="#55FF55")

        except ValueError:
            mostrar_alerta_erro(app, "Modificação Recusada:\nQuantum e número de CPUs devem ser valores inteiros válidos.")

    def editar_tarefa_existente():
        """Permite editar os atributos de uma tarefa específica garantindo a coerência semântica."""
        v_id = entry_id.get().strip()

        if not v_id:
            mostrar_alerta_erro(app, "Operação Recusada:\nInforme o ID da tarefa que deseja alterar.")
            return

        # Procura a tarefa pelo ID informado
        tarefa = next((t for t in tcbs_do_sistema if str(t.id) == str(v_id)), None)

        if not tarefa:
            mostrar_alerta_erro(app, f"Operação Recusada:\nNenhuma tarefa com o ID '{v_id}' foi encontrada no sistema.")
            return

        v_cor = entry_cor.get().strip()
        v_ingresso = entry_ingresso.get().strip()
        v_duracao = entry_duracao.get().strip()
        v_periodo = entry_periodo.get().strip()
        v_prazo = entry_prazo.get().strip()
        v_novo_estado = entry_estado.get().strip().capitalize()

        try:
            # --- VALIDAÇÕES SEMÂNTICAS DURANTE A EXECUÇÃO ---
            
            # 1. Validação do Estado da Tarefa
            if v_novo_estado:
                if v_novo_estado not in ESTADOS_VALIDOS:
                    mostrar_alerta_erro(
                        app, 
                        f"Modificação Semântica Inválida:\nO estado '{v_novo_estado}' não é reconhecido.\n"
                        f"Opções permitidas: {', '.join(ESTADOS_VALIDOS)}"
                    )
                    return

                if simulador and simulador.tempo_global > 0:
                    ocorrencias_tarefa = [o for o in simulador.ocorrencias if o.tarefa is tarefa]

                    # Impede forçar execução de tarefa que ainda não ingressou no tempo global atual
                    if v_novo_estado == "Executando" and not ocorrencias_tarefa:
                        mostrar_alerta_erro(
                            app, 
                            f"Modificação Recusada:\nA tarefa '{v_id}' ainda não chegou ao seu tempo de ingresso ({tarefa.ingresso}). "
                            "Não é possível forçar o estado 'Executando' sem uma instância ativa."
                        )
                        return

                    # Atualiza o estado das ocorrências ativas
                    if v_novo_estado == "Concluída":
                        for o in ocorrencias_tarefa:
                            o.estado = "Concluída"
                            o.tempo_restante = 0

                    elif v_novo_estado in ["Pronta", "Bloqueada"]:
                        for o in ocorrencias_tarefa:
                            if o.estado != "Concluída":
                                o.estado = v_novo_estado

                tarefa.estado = v_novo_estado

            # 2. Validação da Duração da Tarefa
            if v_duracao:
                dur = int(v_duracao)
                if dur <= 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nA duração da tarefa deve ser obrigatoriamente maior que zero.")
                    return
                
                # Impede reduzir a duração para um valor menor do que o tempo que a tarefa já executou
                tempo_ja_executado = getattr(tarefa, 'tempo_execucao', 0)
                if simulador and dur < tempo_ja_executado:
                    mostrar_alerta_erro(
                        app, 
                        f"Modificação Semântica Inválida:\nA tarefa '{v_id}' já executou por {tempo_ja_executado} ticks.\n"
                        f"A nova duração ({dur}) não pode ser menor do que o tempo já processado."
                    )
                    return
                 # Calcula a diferença entre a duração antiga e a nova
                duracao_antiga = tarefa.duracao
                diferenca = dur - duracao_antiga

                # Verifica as ocorrências ainda não concluídas
                if simulador:
                    ocorrencias_ativas = [
                        o for o in simulador.ocorrencias
                        if o.tarefa is tarefa
                        and o.estado != "Concluída"
                    ]

                    # Não permite reduzir a duração abaixo do tempo
                    # já executado por uma ocorrência ativa
                    for o in ocorrencias_ativas:
                        tempo_executado = duracao_antiga - o.tempo_restante

                        if dur < tempo_executado:
                            mostrar_alerta_erro(
                                app,
                                "A nova duração não pode ser menor "
                                "que o tempo já executado pela ocorrência."
                            )
                            return

                    # Atualiza o tempo restante de cada ocorrência
                    for o in ocorrencias_ativas:
                        o.tempo_restante += diferenca

                # Atualiza a duração no TCB
                tarefa.duracao = dur


            # 3. Validação do Tempo de Ingresso
            if v_ingresso:
                ing = int(v_ingresso)
                if ing < 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nO tempo de ingresso não pode ser um número negativo.")
                    return
                
                # Impede alterar o tempo de ingresso para o passado se a tarefa já tiver iniciado execução
                if simulador and simulador.tempo_global > ing and getattr(tarefa, 'tempo_execucao', 0) > 0:
                    mostrar_alerta_erro(
                        app, 
                        f"Modificação Semântica Inválida:\nA tarefa '{v_id}' já começou a executar no tick {tarefa.ingresso}.\n"
                        f"Não é possível alterar o ingresso para o passado ({ing}) durante a simulação."
                    )
                    return
                tarefa.ingresso = ing

            # 4. Validação de Período e Prazo
            if v_periodo:
                per = int(v_periodo)
                if per < 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nO período da tarefa não pode ser negativo.")
                    return
                tarefa.periodo = per

            if v_prazo:
                prz = int(v_prazo)
                if prz <= 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nO prazo (deadline) deve ser maior que zero.")
                    return
                tarefa.prazo = prz

            if v_cor:
                tarefa.cor = v_cor

            if simulador:
                simulador.atualizar_estados()

            atualizar_tabela_tarefas()

            # Limpa os campos do formulário após aplicar as edições
            entry_id.delete(0, 'end')
            entry_cor.delete(0, 'end')
            entry_ingresso.delete(0, 'end')
            entry_duracao.delete(0, 'end')
            entry_periodo.delete(0, 'end')
            entry_prazo.delete(0, 'end')
            entry_estado.delete(0, 'end')

            label_status.configure(text=f"Tarefa {v_id} atualizada!", text_color="#55FF55")

        except ValueError:
            mostrar_alerta_erro(app, "Modificação Recusada:\nOs campos de Ingresso, Duração, Período e Prazo aceitam apenas números inteiros.")

    def abrir_seletor_de_arquivo():
        """Abre caixa de diálogo para carregar e validar um ficheiro de configuração de texto (.txt)."""
        nonlocal tcbs_do_sistema
        caminho_selecionado = filedialog.askopenfilename(
            title="Selecione o arquivo de configuração",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        
        if caminho_selecionado:
            cfg_so, lista_tarefas, erro = validar_configuracao(caminho_selecionado)

            if erro:
                mostrar_alerta_erro(app, erro)
                label_status.configure(text="Aguardando um arquivo válido...", text_color="white")
            else:
                try:
                    # Carrega as configurações globais do SO lidas do ficheiro
                    algoritmo, quantum, qtde_cpus = cfg_so
                    config_so["algoritmo"] = algoritmo.upper()
                    config_so["quantum"] = int(quantum)
                    config_so["cpus"] = int(qtde_cpus)

                    combo_algoritmo.set(config_so["algoritmo"])
                    entry_so_quantum.delete(0, 'end')
                    entry_so_quantum.insert(0, str(config_so["quantum"]))
                    entry_so_cpus.delete(0, 'end')
                    entry_so_cpus.insert(0, str(config_so["cpus"]))

                    # Substitui as tarefas atuais pelas tarefas importadas
                    tcbs_do_sistema.clear()
                    
                    for tarefa in lista_tarefas:
                        v_id, v_cor, v_ingresso, v_duracao, v_periodo, v_prazo, v_lista = tarefa
                        novo_tcb = TCB(
                            id=v_id,
                            cor=v_cor,
                            ingresso=int(v_ingresso),
                            duracao=int(v_duracao),
                            periodo=int(v_periodo),
                            prazo=int(v_prazo),
                            lista_eventos=v_lista
                        )
                        tcbs_do_sistema.append(novo_tcb)
                    
                    carregar_simulador_inicial()
                    
                    mensagem_sucesso = (f"Arquivo carregado: {Path(caminho_selecionado).name}\n"
                                        f"Tarefas: {len(tcbs_do_sistema)}")
                    
                    label_status.configure(text=mensagem_sucesso, text_color="#55FF55")
                    atualizar_tabela_so()
                    atualizar_tabela_tarefas()

                except ValueError as e:
                    mostrar_alerta_erro(
                        app,
                        f"Erro na configuração:\n{str(e)}"
                    )
                    label_status.configure(
                        text="Erro nos dados do arquivo.",
                        text_color="#FF5555"
                    )


    # -------------------------------------------------------------------------
    # CONTROLO DE TEMPO DA SIMULAÇÃO
    # -------------------------------------------------------------------------
    execucao_automatica_ativa = False

    def retroceder_simulacao():
        """Recua o tempo da simulação em 1 tick, restaurando o estado guardado no histórico."""
        if simulador is None or simulador.tempo_global == 0:
            return
        
        simulador.carregar_estado(simulador.tempo_global - 1)

        #sincroniza as tarefas da interface com as tarefas restauradas pelo simulador
        tcbs_do_sistema[:] = simulador.tarefas
        atualizar_graficos_e_tabelas()

    def avancar_simulacao():
        """Avança a simulação em 1 tick de relógio e atualiza a interface."""
        if simulador is None:
            mostrar_alerta_erro(app, "Carregue um arquivo de configuração primeiro para iniciar a simulação.")
            return
            
        simulador.avancar_tick()
        atualizar_graficos_e_tabelas()

    def alternar_execucao_automatica():
        """Alterna entre o modo de pausa e o modo de execução automática contínua."""
        nonlocal execucao_automatica_ativa
        execucao_automatica_ativa = not execucao_automatica_ativa
        
        if execucao_automatica_ativa:
            btn_auto.configure(text="Pausar", fg_color="#e74c3c", hover_color="#c0392b")
            executar_loop_automatico()
        else:
            btn_auto.configure(text="Execução Automática", fg_color="#8e44ad", hover_color="#732d91")

    def executar_loop_automatico():
        """Loop recursivo temporizado para avançar os ticks automaticamente a cada 1 segundo."""
        if execucao_automatica_ativa and not getattr(simulador, 'finalizado', False):
            avancar_simulacao()
            app.after(1000, executar_loop_automatico)

    def atualizar_graficos_e_tabelas():
        """Redesenha todos os componentes visuais do Gantt, tabelas e rótulos de estado."""
        grafico_gantt.desenhar_eixos(tcbs_do_sistema, simulador.tempo_global)
        grafico_gantt.desenhar_execucoes(tcbs_do_sistema, simulador.historico)
        grafico_gantt.desenhar_estados(tcbs_do_sistema, simulador.historico)
        grafico_gantt.desenhar_eventos(tcbs_do_sistema, simulador.eventos_gantt)
        grafico_gantt.desenhar_legenda()       

        label_tick.configure(text=f"Tick atual: {simulador.tempo_global}")
        atualizar_tabela_so()
        atualizar_tabela_tarefas()

        # Interrompe a execução automática e alerta o utilizador se a simulação tiver finalizado
        if getattr(simulador, 'finalizado', False):
            label_status.configure(text="Simulação finalizada!", text_color="#55FF55")
            if execucao_automatica_ativa:
                alternar_execucao_automatica()
    
    def exportar_gantt_png():
        """Abre a caixa de diálogo para salvar a imagem PNG do gráfico de Gantt em alta definição."""
        if simulador is None:
            mostrar_alerta_erro(
                app,
                "Exportação não permitida:\nCarregue e execute uma simulação antes de exportar o gráfico."
            )
            return
        caminho = filedialog.asksaveasfilename(
            title="Salvar gráfico de Gantt",
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")]
        )
        if not caminho:
            return
        try:
            grafico_gantt.exportar_png(
                tarefas=tcbs_do_sistema,
                historico=simulador.historico,
                eventos=simulador.eventos_gantt,
                tempo_maximo=simulador.tempo_global,
                caminho=caminho
            )
            label_status.configure(
                text=f"Gráfico exportado com sucesso em:\n{caminho}",
                text_color="#55FF55"
            )
        except Exception as e:
            mostrar_alerta_erro(
                app,
                f"Erro ao exportar o gráfico:\n{str(e)}"
            )

    # -------------------------------------------------------------------------
    # LAYOUT E CONSTRUÇÃO DOS PAINÉIS DA INTERFACE
    # -------------------------------------------------------------------------
    painel_esquerdo = ctk.CTkFrame(app, width=420)
    painel_esquerdo.pack(side="left", fill="both", padx=10, pady=10)

    painel_direito = ctk.CTkFrame(app)
    painel_direito.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # --- PAINEL ESQUERDO: CONTROLES E FORMULÁRIOS ---
    titulo = ctk.CTkLabel(painel_esquerdo, text="Painel de Controle", font=("Arial", 18, "bold"))
    titulo.pack(pady=(10, 5))

    btn_carregar = ctk.CTkButton(painel_esquerdo, text="Carregar Arquivo .TXT", command=abrir_seletor_de_arquivo)
    btn_carregar.pack(pady=10)

    label_status = ctk.CTkLabel(painel_esquerdo, text="Aguardando arquivo...", justify="center", wraplength=320)
    label_status.pack(pady=5)

    frame_scroll_forms = ctk.CTkScrollableFrame(painel_esquerdo)
    frame_scroll_forms.pack(fill="both", expand=True, padx=5, pady=10)

    # 1. Formulário do Sistema Operacional
    lbl_so_titulo = ctk.CTkLabel(
        frame_scroll_forms, 
        text="Configuração do SO", 
        font=("Arial", 14, "bold"),
        wraplength=300,
        anchor="w"
    )
    lbl_so_titulo.pack(fill="x", padx=10, pady=(10, 5))

    ctk.CTkLabel(frame_scroll_forms, text="Algoritmo de Escalonamento:", font=("Arial", 12)).pack(anchor="w", padx=10)
    combo_algoritmo = ctk.CTkOptionMenu(frame_scroll_forms, values=["RM", "EDF"])
    combo_algoritmo.set(VALORES_PADRAO_SO["algoritmo"])
    combo_algoritmo.pack(fill="x", padx=10, pady=(0, 5))

    ctk.CTkLabel(frame_scroll_forms, text="Quantum:", font=("Arial", 12)).pack(anchor="w", padx=10)
    entry_so_quantum = ctk.CTkEntry(frame_scroll_forms)
    entry_so_quantum.insert(0, str(VALORES_PADRAO_SO["quantum"]))
    entry_so_quantum.pack(fill="x", padx=10, pady=(0, 5))

    ctk.CTkLabel(frame_scroll_forms, text="Quantidade de CPUs:", font=("Arial", 12)).pack(anchor="w", padx=10)
    entry_so_cpus = ctk.CTkEntry(frame_scroll_forms)
    entry_so_cpus.insert(0, str(VALORES_PADRAO_SO["cpus"]))
    entry_so_cpus.pack(fill="x", padx=10, pady=(0, 5))

    btn_aplicar_so = ctk.CTkButton(frame_scroll_forms, text="Aplicar Modificações no SO", command=aplicar_config_so, fg_color="#1f538d")
    btn_aplicar_so.pack(pady=10)

    ctk.CTkFrame(frame_scroll_forms, height=2, fg_color="#333333").pack(fill="x", padx=10, pady=10)

    # 2. Formulário de Edição/Configuração de Tarefas
    lbl_form_titulo = ctk.CTkLabel(
        frame_scroll_forms, 
        text="Modificar / Configurar Tarefa", 
        font=("Arial", 14, "bold"),
        wraplength=300,
        anchor="w"
    )
    lbl_form_titulo.pack(fill="x", padx=10, pady=5)

    def criar_campo(label_text, placeholder=""):
        """Função auxiliar para construir rótulos e campos de texto padronizados."""
        lbl = ctk.CTkLabel(frame_scroll_forms, text=label_text, font=("Arial", 12))
        lbl.pack(anchor="w", padx=10, pady=(5, 0))
        entry = ctk.CTkEntry(frame_scroll_forms, placeholder_text=placeholder, text_color="#FBFFFF")
        entry.pack(fill="x", padx=10, pady=(0, 5))
        return entry

    entry_id = criar_campo("ID da tarefa (obrigatório):", "Ex: T1")
    entry_estado = criar_campo("Novo Estado:", "Nova, Pronta, Executando...")
    entry_cor = criar_campo("Nova Cor:", "Ex: Azul")
    entry_ingresso = criar_campo("Novo Ingresso:", "Ex: 0")
    entry_duracao = criar_campo("Nova Duração:", "Ex: 4")
    entry_periodo = criar_campo("Novo Período:", "Ex: 10")
    entry_prazo = criar_campo("Novo Prazo:", "Ex: 8")

    btn_atualizar = ctk.CTkButton(frame_scroll_forms, text="Salvar Alterações na Tarefa", command=editar_tarefa_existente, fg_color="#1f538d")
    btn_atualizar.pack(pady=15)

    # --- PAINEL DIREITO: TABELAS, VISUALIZAÇÃO GANTT E CONTROLO ---
    lbl_tabela_so = ctk.CTkLabel(painel_direito, text="Configurações Atuais do Sistema Operacional", font=("Arial", 16, "bold"))
    lbl_tabela_so.pack(pady=(10, 5))

    frame_tabela_so_container = ctk.CTkFrame(painel_direito, fg_color="transparent")
    frame_tabela_so_container.pack(fill="x", padx=10, pady=5)

    lbl_tabela_tarefas = ctk.CTkLabel(painel_direito, text="Tabela de Tarefas e Características", font=("Arial", 16, "bold"))
    lbl_tabela_tarefas.pack(pady=(15, 5))

    frame_tabela_tarefas_container = ctk.CTkScrollableFrame(painel_direito)
    frame_tabela_tarefas_container.pack(fill="both", expand=True, padx=10, pady=5)

    # Barra inferior de controlo fixada na parte inferior
    frame_controle = ctk.CTkFrame(painel_direito, fg_color="transparent")
    frame_controle.pack(side="bottom", fill="x", pady=10)

    label_tick = ctk.CTkLabel(frame_controle, text="Tick atual: 0", font=("Arial", 14, "bold"))
    label_tick.pack(side="left", padx=20)

    btn_auto = ctk.CTkButton(frame_controle, text="Execução Automática", command=alternar_execucao_automatica, fg_color="#8e44ad", hover_color="#732d91")
    btn_auto.pack(side="right", padx=10)

    btn_avancar = ctk.CTkButton(frame_controle, text="Avançar Tick", command=avancar_simulacao, fg_color="#27ae60", hover_color="#219150")
    btn_avancar.pack(side="right", padx=10)
    
    btn_retroceder = ctk.CTkButton(frame_controle, text="Retroceder Tick", command=retroceder_simulacao, fg_color="#f39c12", hover_color="#d68910")
    btn_retroceder.pack(side="right", padx=10)

    btn_exportar = ctk.CTkButton(
        frame_controle,
        text="Exportar Gantt (PNG)",
        command=exportar_gantt_png,
        fg_color="#34495e",
        hover_color="#2c3e50"
    )
    btn_exportar.pack(side="right", padx=10)

    # Área do gráfico de Gantt com scrollbar horizontal
    lbl_gantt = ctk.CTkLabel(painel_direito, text="Gráfico de Gantt", font=("Arial", 16, "bold"))
    lbl_gantt.pack(pady=(10, 5))
    
    frame_scroll_gantt = ctk.CTkScrollableFrame(painel_direito, orientation="horizontal", fg_color="transparent")
    frame_scroll_gantt.pack(fill="both", expand=True, padx=10, pady=5)

    # Instanciação do componente do Gráfico de Gantt
    grafico_gantt = GraficoGantt(frame_scroll_gantt)
    grafico_gantt.pack(fill="both", expand=True)

    # Execuções de arranque: renderiza as tabelas e inicializa o simulador
    atualizar_tabela_so()
    atualizar_tabela_tarefas()
    carregar_simulador_inicial()

    # Inicia o loop principal de eventos da interface gráfica
    app.mainloop()

if __name__ == "__main__":
    start_interface()