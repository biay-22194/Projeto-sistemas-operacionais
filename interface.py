import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from dataclasses import dataclass, field
from structs import TCB
from utils import validar_configuracao
from simulator import Simulador

# ----------------------------------------------------------------------------------------------------------------------------------------------
# INTERFACE GRÁFICA E POP-UPS
def mostrar_alerta_erro(parent_app, mensagem):
    
    # Cria uma janela pop-up modal
    popup = ctk.CTkToplevel(parent_app)
    popup.title("Erro de Configuração")
    popup.geometry("400x150")
    popup.grab_set() 
    popup.focus() # Foca na janela de erro

    lbl_erro = ctk.CTkLabel(popup, text=mensagem, text_color="#FF5555", wraplength=350)
    lbl_erro.pack(pady=30, padx=10)

    btn_fechar = ctk.CTkButton(popup, text="OK", command=popup.destroy, width=100)
    btn_fechar.pack(pady=5)


def start_interface():

    # Configuração inicial da janela
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("Simulador visual de sistema operacional")
    app.geometry("500x400")
    simulador = None

    def abrir_seletor_de_arquivo():
        nonlocal simulador
        caminho_selecionado = filedialog.askopenfilename(
            title="Selecione o arquivo de configuração",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        
        if caminho_selecionado:
            config_so, lista_tarefas, erro = validar_configuracao(caminho_selecionado)

            if erro:
                # Se houver erro, chama a janela pop-up e mantém o label original aguardando
                mostrar_alerta_erro(app, erro)
                label_status.configure(text="Aguardando um arquivo válido...", text_color="white")
            else:
                try:
                    # Desempacota as variáveis do SO
                    algoritmo, quantum, qtde_cpus = config_so
                    
                    # Cria as TCBs para o sistema
                    tcbs_do_sistema = []
                    
                    for tarefa in lista_tarefas:
                        v_id, v_cor, v_ingresso, v_duracao, v_periodo, v_prazo, v_lista = tarefa
                        
                        # Converte e cria a struct TCB
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
                    
                    

                    simulador = Simulador(tcbs_do_sistema)# Atualiza a interface
                    mensagem_sucesso = (f"Arquivo: {Path(caminho_selecionado).name}\n"
                                        f"Algoritmo: {algoritmo.upper()} | Quantum: {quantum}\n"
                                        f"Tarefas carregadas: {len(tcbs_do_sistema)}")
                    
                    label_status.configure(text=mensagem_sucesso, text_color="#55FF55")
                    
                    # Exemplo de print no terminal para debug
                    print(f"Sucesso! {len(tcbs_do_sistema)} tarefas prontas para execução.")

                except ValueError as e:
                    # Caso o usuário tenha colocado letras no lugar de números na duração, prazo...
                    erro_conversao = "Erro: Esperava-se números no ingresso, duração, período ou prazo, mas encontrou-se texto."
                    mostrar_alerta_erro(app, erro_conversao)
                    label_status.configure(text="Erro nos dados do arquivo.", text_color="#FF5555")

        else:
            label_status.configure(text="Operação cancelada.", text_color="white")

    # Widgets da Interface
    titulo = ctk.CTkLabel(app, text="Escolha seu arquivo de configuração", font=("Arial", 20, "bold"))
    titulo.pack(pady=20)

    btn_carregar = ctk.CTkButton(app, text="Carregar configuração", command=abrir_seletor_de_arquivo)
    btn_carregar.pack(pady=20)

    label_status = ctk.CTkLabel(app, text="Aguardando arquivo...", justify="center")
    label_status.pack(pady=20)

    def avancar_simulacao():
        if simulador is None:
            mostrar_alerta_erro(app, "Carregue um arquivo primeiro.")
            return
    
        simulador.avancar_tick()
    
        label_tick.configure(
            text=f"Tick atual: {simulador.tempo_global}"
        )
    
        if simulador.finalizado:
            label_status.configure(
                text="Simulação finalizada!",
                text_color="#55FF55"
            )


    btn_avancar = ctk.CTkButton(
        app,
        text="Avançar Tick",
        command=avancar_simulacao
    )
    btn_avancar.pack(pady=10)

    label_tick = ctk.CTkLabel(
        app,
        text="Tick atual: 0"
    )
    label_tick.pack(pady=10)
    app.mainloop()
