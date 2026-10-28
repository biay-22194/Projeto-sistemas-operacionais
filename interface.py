import customtkinter as ctk
from gantt import GraficoGantt
from CTkTable import CTkTable
from tkinter import filedialog
from pathlib import Path
from dataclasses import dataclass, field
from structs import TCB, RateMonotonic, EarliestDeadlineFirst
from utils import validar_configuracao
from simulator import Simulador

# Estados válidos
ESTADOS_VALIDOS = ["Nova", "Pronta", "Executando", "Bloqueada", "Concluída"]

# ----------------------------------------------------------------------------------------------------------------------------------------------
# INTERFACE GRÁFICA E POP-UPS
def mostrar_alerta_erro(parent_app, mensagem):
    popup = ctk.CTkToplevel(parent_app)
    popup.title("Alteração Não Permitida")
    popup.geometry("450x180")
    
    # Evita erros de renderização no Linux
    popup.transient(parent_app)
    popup.wait_visibility()
    popup.grab_set() 
    popup.focus()

    lbl_erro = ctk.CTkLabel(
        popup, 
        text=mensagem, 
        text_color="#FF5555", 
        wraplength=410, 
        font=("Arial", 12),
        justify="left"
    )
    lbl_erro.pack(pady=20, padx=15)

    btn_fechar = ctk.CTkButton(popup, text="Entendido", command=popup.destroy, width=110)
    btn_fechar.pack(pady=5)


def start_interface():
    ctk.set_appearance_mode("dark")
    
    app = ctk.CTk()
    app.title("Simulador Visual de Sistema Operacional")
    app.geometry("1100x750")
    
    simulador = None
    tcbs_do_sistema = []
    
    # -------------------------------------------------------------------------
    # VALORES PADRÃO DA SIMULAÇÃO 
    # -------------------------------------------------------------------------
    VALORES_PADRAO_SO = {
        "algoritmo": "RM",
        "quantum": 2,
        "cpus": 1
    }
    
    config_so = VALORES_PADRAO_SO.copy()

    tabela_so_widget = None
    tabela_tarefas_widget = None

    # -------------------------------------------------------------------------
    # RENDERIZAÇÃO DAS TABELAS
    # -------------------------------------------------------------------------
    def atualizar_tabela_so():
        nonlocal tabela_so_widget
        
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

        tabela_so_widget = CTkTable(
            master=frame_tabela_so_container,
            values=dados_so,
            header_color="#1f538d",
            colors=["#2b2b2b", "#333333"]
        )
        tabela_so_widget.pack(expand=True, fill="both", padx=5, pady=5)

    def atualizar_tabela_tarefas():
        nonlocal tabela_tarefas_widget
        
        if tabela_tarefas_widget is not None:
            tabela_tarefas_widget.destroy()

        dados_tarefas = [["ID", "Cor", "Ingresso", "Duração", "Período", "Prazo", "Estado Atual"]]
        
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
        nonlocal simulador
        if not tcbs_do_sistema:
            simulador = None
            return

        alg_nome = config_so["algoritmo"].upper()
        quantum_val = config_so["quantum"]
        cpus_val = config_so["cpus"]

        if alg_nome == "RM":
            escalonador = RateMonotonic(quantum=quantum_val)
        elif alg_nome == "EDF":
            escalonador = EarliestDeadlineFirst(quantum=quantum_val)
        else:
            raise ValueError("Algoritmo inválido.")

        simulador = Simulador(
            tarefas=tcbs_do_sistema,
            algoritmo=escalonador,
            qtde_cpus=cpus_val
        )
        label_tick.configure(text="Tick atual: 0")

    # -------------------------------------------------------------------------
    # MODIFICAÇÕES ANTES E DURANTE A EXECUÇÃO COM JUSTIFICATIVA 
    # -------------------------------------------------------------------------
    def aplicar_config_so():
        try:
            novo_alg = combo_algoritmo.get().strip().upper()
            txt_quantum = entry_so_quantum.get().strip()
            txt_cpus = entry_so_cpus.get().strip()

            q_val = int(txt_quantum) if txt_quantum else config_so["quantum"]
            c_val = int(txt_cpus) if txt_cpus else config_so["cpus"]

            if q_val <= 0:
                mostrar_alerta_erro(app, "Modificação Recusada:\nO Quantum precisa ser um número maior que zero (>= 1).")
                return

            if c_val <= 0:
                mostrar_alerta_erro(app, "Modificação Recusada:\nO sistema necessita de pelo menos 1 CPU ativa para funcionar.")
                return

            config_so["algoritmo"] = novo_alg
            config_so["quantum"] = q_val
            config_so["cpus"] = c_val

            # Aplicação dinâmica sem resetar simulação em andamento
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
        v_id = entry_id.get().strip()

        if not v_id:
            mostrar_alerta_erro(app, "Operação Recusada:\nInforme o ID da tarefa que deseja alterar.")
            return

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
            
            # 1. Validação do Estado
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

                    if v_novo_estado == "Executando" and not ocorrencias_tarefa:
                        mostrar_alerta_erro(
                            app, 
                            f"Modificação Recusada:\nA tarefa '{v_id}' ainda não chegou ao seu tempo de ingresso ({tarefa.ingresso}). "
                            "Não é possível forçar o estado 'Executando' sem uma instância ativa."
                        )
                        return

                    if v_novo_estado == "Concluída":
                        for o in ocorrencias_tarefa:
                            o.estado = "Concluída"
                            o.tempo_restante = 0

                    elif v_novo_estado in ["Pronta", "Bloqueada"]:
                        for o in ocorrencias_tarefa:
                            if o.estado != "Concluída":
                                o.estado = v_novo_estado

                tarefa.estado = v_novo_estado

            # 2. Validação de Duração
            if v_duracao:
                dur = int(v_duracao)
                if dur <= 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nA duração da tarefa deve ser obrigatoriamente maior que zero.")
                    return
                
                tempo_ja_executado = getattr(tarefa, 'tempo_execucao', 0)
                if simulador and dur < tempo_ja_executado:
                    mostrar_alerta_erro(
                        app, 
                        f"Modificação Semântica Inválida:\nA tarefa '{v_id}' já executou por {tempo_ja_executado} ticks.\n"
                        f"A nova duração ({dur}) não pode ser menor do que o tempo já processado."
                    )
                    return
                tarefa.duracao = dur

            # 3. Validação de Ingresso
            if v_ingresso:
                ing = int(v_ingresso)
                if ing < 0:
                    mostrar_alerta_erro(app, "Modificação Recusada:\nO tempo de ingresso não pode ser um número negativo.")
                    return
                
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

            # Limpa entradas
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
                    algoritmo, quantum, qtde_cpus = cfg_so
                    config_so["algoritmo"] = algoritmo.upper()
                    config_so["quantum"] = int(quantum)
                    config_so["cpus"] = int(qtde_cpus)

                    combo_algoritmo.set(config_so["algoritmo"])
                    entry_so_quantum.delete(0, 'end')
                    entry_so_quantum.insert(0, str(config_so["quantum"]))
                    entry_so_cpus.delete(0, 'end')
                    entry_so_cpus.insert(0, str(config_so["cpus"]))

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

                except ValueError:
                    erro_conversao = "Erro: Esperava-se números inteiros nos parâmetros do arquivo."
                    mostrar_alerta_erro(app, erro_conversao)
                    label_status.configure(text="Erro nos dados do arquivo.", text_color="#FF5555")

    def avancar_simulacao():
        if simulador is None:
            mostrar_alerta_erro(app, "Carregue um arquivo de configuração primeiro para iniciar a simulação.")
            return
    
        simulador.avancar_tick()
        grafico_gantt.desenhar_eixos(
            tcbs_do_sistema,
            simulador.tempo_global
        )

        grafico_gantt.desenhar_execucoes(
            tcbs_do_sistema,
            simulador.historico
        )

        grafico_gantt.desenhar_estados(
            tcbs_do_sistema,
            simulador.historico
        )

        grafico_gantt.desenhar_eventos(
            tcbs_do_sistema,
            simulador.eventos_gantt
)
        grafico_gantt.desenhar_legenda()       

        label_tick.configure(text=f"Tick atual: {simulador.tempo_global}")
        atualizar_tabela_so()
        atualizar_tabela_tarefas()
    
        if getattr(simulador, 'finalizado', False):
            label_status.configure(text="Simulação finalizada!", text_color="#55FF55")

        print("Histórico:", simulador.historico)
        print("Eventos Gantt:", simulador.eventos_gantt)

    # -------------------------------------------------------------------------
    # LAYOUT DA INTERFACE
    # -------------------------------------------------------------------------
    painel_esquerdo = ctk.CTkFrame(app, width=420)
    painel_esquerdo.pack(side="left", fill="both", padx=10, pady=10)

    painel_direito = ctk.CTkFrame(app)
    painel_direito.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # --- PAINEL ESQUERDO ---
    titulo = ctk.CTkLabel(painel_esquerdo, text="Painel de Controle", font=("Arial", 18, "bold"))
    titulo.pack(pady=(10, 5))

    btn_carregar = ctk.CTkButton(painel_esquerdo, text="Carregar Arquivo .TXT", command=abrir_seletor_de_arquivo)
    btn_carregar.pack(pady=10)

    label_status = ctk.CTkLabel(painel_esquerdo, text="Aguardando arquivo...", justify="center", wraplength=320)
    label_status.pack(pady=5)

    frame_scroll_forms = ctk.CTkScrollableFrame(painel_esquerdo)
    frame_scroll_forms.pack(fill="both", expand=True, padx=5, pady=10)

    # 1. FORMULÁRIO SO COM VALORES PADRÃO (Req 3.2)
    lbl_so_titulo = ctk.CTkLabel(
        frame_scroll_forms, 
        text="Configuração do SO", 
        font=("Arial", 14, "bold"),
        wraplength=300,  # Limita o texto para não ultrapassar a barra
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

    # 2. FORMULÁRIO TAREFAS COM SUGESTÕES PADRÃO (Req 3.2)
    lbl_form_titulo = ctk.CTkLabel(
        frame_scroll_forms, 
        text="Modificar / Configurar Tarefa", 
        font=("Arial", 14, "bold"),
        wraplength=300,
        anchor="w"
    )
    lbl_form_titulo.pack(fill="x", padx=10, pady=5)

    def criar_campo(label_text, placeholder=""):
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

    # --- PAINEL DIREITO ---
    lbl_tabela_so = ctk.CTkLabel(painel_direito, text="Configurações Atuais do Sistema Operacional", font=("Arial", 16, "bold"))
    lbl_tabela_so.pack(pady=(10, 5))

    frame_tabela_so_container = ctk.CTkFrame(painel_direito, fg_color="transparent")
    frame_tabela_so_container.pack(fill="x", padx=10, pady=5)

    lbl_tabela_tarefas = ctk.CTkLabel(painel_direito, text="Tabela de Tarefas e Características", font=("Arial", 16, "bold"))
    lbl_tabela_tarefas.pack(pady=(15, 5))

    frame_tabela_tarefas_container = ctk.CTkScrollableFrame(painel_direito)
    frame_tabela_tarefas_container.pack(fill="both", expand=True, padx=10, pady=5)

    # Área do gráfico de Gantt
    lbl_gantt = ctk.CTkLabel(
        painel_direito,
        text="Gráfico de Gantt",
        font=("Arial", 16, "bold")
    )
    lbl_gantt.pack(pady=(10, 5))

    grafico_gantt = GraficoGantt(painel_direito)
    grafico_gantt.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=5
    )
    frame_controle = ctk.CTkFrame(painel_direito, fg_color="transparent")
    frame_controle.pack(fill="x", pady=10)

    label_tick = ctk.CTkLabel(frame_controle, text="Tick atual: 0", font=("Arial", 14, "bold"))
    label_tick.pack(side="left", padx=20)

    btn_avancar = ctk.CTkButton(frame_controle, text="Avançar Tick", command=avancar_simulacao, fg_color="#27ae60", hover_color="#219150")
    btn_avancar.pack(side="right", padx=20)

    atualizar_tabela_so()
    atualizar_tabela_tarefas()

    app.mainloop()

if __name__ == "__main__":
    start_interface()