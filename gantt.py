import tkinter as tk
from PIL import Image, ImageDraw, ImageFont

class GraficoGantt(tk.Frame):
    """
    Componente visual responsável pela renderização do Gráfico de Gantt
    e exportação de imagens de alta resolução da simulação do SO.
    """

    def __init__(self, master):
        """Inicializa a estrutura do Frame e o Canvas interativo."""
        super().__init__(master)

        # Canvas Tkinter com fundo escuro para desenho dos elementos visuais
        self.canvas = tk.Canvas(
            self,
            bg="#202020",
            height=300,
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )
    
    def desenhar_eixos(self, tarefas, tempo_maximo):
        """
        Limpa o gráfico e desenha a grelha de eixos do Gantt:
        - Eixo X (Superior): Marcadores de ticks de tempo.
        - Eixo Y (Esquerdo): IDs das tarefas ordenados alfabeticamente.
        """
        # Limpa todos os elementos desenhados anteriormente no Canvas
        self.canvas.delete("all")

        # Parâmetros de espaçamento e dimensão da "grade"
        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        # Ordena as tarefas pelo ID para manter a consistência no eixo Y
        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

        # --- Eixo Horizontal: Tempo (Ticks) ---
        for tempo in range(tempo_maximo + 1):
            x = margem_esquerda + tempo * largura_tick

            # Rótulo numérico do tempo
            self.canvas.create_text(
                x,
                margem_superior - 15,
                text=str(tempo),
                fill="white"
            )

            # Linha vertical da grade
            self.canvas.create_line(
                x,
                margem_superior,
                x,
                margem_superior + len(tarefas_ordenadas) * altura_linha,
                fill="#444444"
            )

        # --- Eixo Vertical: Tarefas ---
        for indice, tarefa in enumerate(tarefas_ordenadas):
            y = margem_superior + indice * altura_linha

            # Identificador da tarefa no eixo Y
            self.canvas.create_text(
                margem_esquerda - 15,
                y + altura_linha / 2,
                text=str(tarefa.id),
                fill="white",
                anchor="e"
            )

            # Linha horizontal da grade de cada tarefa
            self.canvas.create_line(
                margem_esquerda,
                y + altura_linha,
                margem_esquerda + tempo_maximo * largura_tick,
                y + altura_linha,
                fill="#444444"
            )

    def desenhar_execucoes(self, tarefas, historico):
        """
        Desenha os blocos coloridos de execução das tarefas e indica
        o número do processador (CPU) que executou em cada tick.
        """
        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

        # Percorre o histórico de estados filtrando apenas instâncias em execução
        for registro in historico:
            if registro["estado"] != "Executando":
                continue

            tarefa = next(
                (t for t in tarefas_ordenadas
                 if str(t.id) == str(registro["tarefa"])),
                None
            )

            if tarefa is None:
                continue

            indice = tarefas_ordenadas.index(tarefa)

            # Coordenadas do bloco de execução
            x1 = margem_esquerda + registro["tempo"] * largura_tick
            x2 = x1 + largura_tick
            y1 = margem_superior + indice * altura_linha + 5
            y2 = y1 + 30

            cor = tarefa.cor

            # Garante que a cor hexadecimal possui a formatação válida ('#')
            if not cor.startswith("#"):
                try:
                    self.canvas.winfo_rgb(cor)
                except tk.TclError:
                    cor = "#" + cor

            # Desenha o retângulo preenchido com a cor da tarefa
            try:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=cor,
                    outline="white"
                )
            except tk.TclError:
                # Cor padrão em caso de erro no nome/código hexadecimal
                cor = "#777777"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=cor,
                    outline="white"
                )

            # Rótulo indicativo do ID da CPU no centro do bloco
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=str(registro["cpu"]),
                fill="white",
                font=("Arial", 10, "bold")
            )

    def desenhar_estados(self, tarefas, historico):
        """
        Desenha os marcadores de estado intermediários:
        - 'P' (Retângulo vazio com borda): Tarefa na fila de Prontas.
        - 'X' (Retângulo cinzento com cruz): Tarefa no estado Bloqueada/Suspensa.
        """
        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

        for registro in historico:
            estado = registro["estado"]

            if estado not in ("Pronta", "Bloqueada"):
                continue

            tarefa = next(
                (t for t in tarefas_ordenadas
                 if str(t.id) == str(registro["tarefa"])),
                None
            )

            if tarefa is None:
                continue

            indice = tarefas_ordenadas.index(tarefa)

            x1 = margem_esquerda + registro["tempo"] * largura_tick
            x2 = x1 + largura_tick
            y1 = margem_superior + indice * altura_linha + 5
            y2 = y1 + 30

            if estado == "Pronta":
                # Bloco para indicação de fila de espera
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="#202020",
                    outline="#FFFFFF",
                    width=2
                )
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text="P",
                    fill="white"
                )

            elif estado == "Bloqueada":
                # Bloco para indicação de suspensão/bloqueio
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="#555555",
                    outline="white"
                )
                # X vermelho 
                self.canvas.create_line(
                    x1 + 5, y1 + 5,
                    x2 - 5, y2 - 5,
                    fill="white",
                    width=2
                )
                self.canvas.create_line(
                    x1 + 5, y2 - 5,
                    x2 - 5, y1 + 5,
                    fill="white",
                    width=2
                )

    def desenhar_eventos(self, tarefas, eventos):
        """
        Renderiza os símbolos geométricos pontuais:
        - Triângulo Verde: Chegada de uma nova tarefa.
        - Círculo Azul: Conclusão com sucesso de uma instância.
        - X vermelho: Violação/Perda do prazo estipulado (Deadline miss).
        """
        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

        for evento in eventos:
            tarefa_id = str(evento["tarefa"])

            indice = next(
                (
                    i for i, tarefa in enumerate(tarefas_ordenadas)
                    if str(tarefa.id) == tarefa_id
                ),
                None
            )

            if indice is None:
                continue

            x = margem_esquerda + evento["tempo"] * largura_tick
            y = margem_superior + indice * altura_linha
            tipo = evento["tipo"]

            if tipo == "Chegada":
                # Símbolo em forma de triângulo verde
                self.canvas.create_polygon(
                    x, y + 2,
                    x - 6, y + 12,
                    x + 6, y + 12,
                    fill="#2ECC71"
                )

            elif tipo == "Conclusão":
                # Símbolo em forma de círculo azul
                self.canvas.create_oval(
                    x - 5, y + 3,
                    x + 5, y + 13,
                    fill="#3498DB",
                    outline="white"
                )

            elif tipo == "Perda de prazo":
                # Desenha o 'X' 
                self.canvas.create_line(
                    x - 5, y + 3, x + 5, y + 13, 
                    fill="#FF4444", width=3
                )
                self.canvas.create_line(
                    x - 5, y + 13, x + 5, y + 3, 
                    fill="#FF4444", width=3
                )
    
    def desenhar_legenda(self):
        """
        Exibe a legenda explicativa de cores e símbolos na parte superior
        e atualiza dinamicamente a scrollregion para ativar a rolagem horizontal.
        """
        y = 15

        # Legenda: Executando
        self.canvas.create_rectangle(
            70, y - 7, 85, y + 7,
            fill="#3498DB",
            outline="white"
        )
        self.canvas.create_text(
            90, y,
            text="Executando",
            fill="white",
            anchor="w"
        )

        # Legenda: Pronta
        self.canvas.create_rectangle(
            190, y - 7, 205, y + 7,
            fill="#202020",
            outline="white",
            width=2
        )
        self.canvas.create_text(
            210, y,
            text="Pronta",
            fill="white",
            anchor="w"
        )

        # Legenda: Bloqueada
        self.canvas.create_rectangle(
            280, y - 7, 295, y + 7,
            fill="#555555",
            outline="white"
        )
        self.canvas.create_line(
            282, y - 5, 293, y + 5,
            fill="white"
        )
        self.canvas.create_line(
            282, y + 5, 293, y - 5,
            fill="white"
        )
        self.canvas.create_text(
            300, y,
            text="Bloqueada",
            fill="white",
            anchor="w"
        )

        # Legenda de Eventos Pontuais
        y = 35

        # Chegada
        self.canvas.create_polygon(
            75, y - 6,
            69, y + 4,
            81, y + 4,
            fill="#2ECC71"
        )
        self.canvas.create_text(
            90, y,
            text="Chegada",
            fill="white",
            anchor="w"
        )

        # Conclusão
        self.canvas.create_oval(
            190, y - 5, 200, y + 5,
            fill="#3498DB",
            outline="white"
        )
        self.canvas.create_text(
            210, y,
            text="Conclusão",
            fill="white",
            anchor="w"
        )

        # Prazo Perdido
        self.canvas.create_line(
            285, y - 5, 295, y + 5,
            fill="#FF4444", width=3
        )
        self.canvas.create_line(
            285, y + 5, 295, y - 5,
            fill="#FF4444", width=3
        )
        self.canvas.create_text(
            305, y,
            text="Prazo perdido",
            fill="white",
            anchor="w"
        )

        # Ajuste dinâmico do container para permitir a rolagem horizontal
        caixa = self.canvas.bbox("all")
        if caixa:
            largura_total = caixa[2] + 50
            self.canvas.configure(scrollregion=caixa, width=largura_total)
            self.configure(width=largura_total)
    
    def exportar_png(self, tarefas, historico, eventos, tempo_maximo, caminho):
        """
        Converte o desenho vetorial do Canvas em uma imagem PNG em alta definição.
        """
        caixa = self.canvas.bbox("all")
        largura = caixa[2] - caixa[0] + 50 if caixa else 1000
        altura = caixa[3] - caixa[1] + 50 if caixa else 800

        # Injeta um retângulo escuro temporário no fundo para garantir leitura no PNG exportado
        fundo_id = self.canvas.create_rectangle(
            -50, -50, largura + 50, altura + 50, 
            fill="#202020", outline="#202020"
        )
        self.canvas.tag_lower(fundo_id)

        # Captura do buffer vetorial PostScript do Canvas
        ps = self.canvas.postscript(colormode='color', width=largura, height=altura, x=0, y=0)
        
        # Remove o retângulo de fundo temporário da interface gráfica ativa
        self.canvas.delete(fundo_id)
        
        import io
        from PIL import Image
        
        # Carrega os dados PostScript usando Pillow e força redimensionamento escalar 4x (Alta Definição)
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.load(scale=4) 
        
        # Salva o arquivo final no formato PNG
        img.save(caminho, "png")

