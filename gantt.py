import tkinter as tk
from PIL import Image, ImageDraw, ImageFont

class GraficoGantt(tk.Frame):

    def __init__(self, master):
        super().__init__(master)

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

        self.canvas.delete("all")

        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

        # Eixo horizontal: tempo
        for tempo in range(tempo_maximo + 1):

            x = margem_esquerda + tempo * largura_tick

            self.canvas.create_text(
                x,
                margem_superior - 15,
                text=str(tempo),
                fill="white"
            )

            self.canvas.create_line(
                x,
                margem_superior,
                x,
                margem_superior + len(tarefas_ordenadas) * altura_linha,
                fill="#444444"
            )

        # Eixo vertical: tarefas
        for indice, tarefa in enumerate(tarefas_ordenadas):

            y = margem_superior + indice * altura_linha

            self.canvas.create_text(
                margem_esquerda - 15,
                y + altura_linha / 2,
                text=str(tarefa.id),
                fill="white",
                anchor="e"
            )

            self.canvas.create_line(
                margem_esquerda,
                y + altura_linha,
                margem_esquerda + tempo_maximo * largura_tick,
                y + altura_linha,
                fill="#444444"
            )

    def desenhar_execucoes(self, tarefas, historico):

        margem_esquerda = 70
        margem_superior = 85
        altura_linha = 40
        largura_tick = 40

        tarefas_ordenadas = sorted(
            tarefas,
            key=lambda tarefa: str(tarefa.id)
        )

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

            x1 = margem_esquerda + registro["tempo"] * largura_tick
            x2 = x1 + largura_tick

            y1 = margem_superior + indice * altura_linha + 5
            y2 = y1 + 30

            cor = tarefa.cor

            if not cor.startswith("#"):
                try:
                    self.canvas.winfo_rgb(cor)
                except tk.TclError:
                    cor = "#" + cor

            try:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=cor,
                    outline="white"
                )
            except tk.TclError:
                cor = "#777777"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=cor,
                    outline="white"
                )

            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=str(registro["cpu"]),
                fill="white",
                font=("Arial", 10, "bold")
            )

    def desenhar_estados(self, tarefas, historico):

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

                # Retângulo vazio com contorno colorido
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

                # Retângulo cinza
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="#555555",
                    outline="white"
                )

                # Desenha um X
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

                self.canvas.create_polygon(
                    x, y + 2,
                    x - 6, y + 12,
                    x + 6, y + 12,
                    fill="#2ECC71"
                )

            elif tipo == "Conclusão":

                self.canvas.create_oval(
                    x - 5, y + 3,
                    x + 5, y + 13,
                    fill="#3498DB",
                    outline="white"
                )

            elif tipo == "Perda de prazo":

                self.canvas.create_text(
                    x,
                    y + 8,
                    text="✕",
                    fill="#FF4444",
                    font=("Arial", 16, "bold")
                )
    
    def desenhar_legenda(self):

        y = 15

        # Executando
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

        # Pronta
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

        # Bloqueada
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

        # Eventos
        y = 35

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

        self.canvas.create_text(
            290, y,
            text="✕",
            fill="#FF4444",
            font=("Arial", 16, "bold")
        )
        self.canvas.create_text(
            305, y,
            text="Prazo perdido",
            fill="white",
            anchor="w"
        )
    
    def exportar_png(self, tarefas, historico, eventos, tempo_maximo, caminho):
        
        margem_esquerda = 100
        margem_superior = 100
        largura_tick = 40
        altura_linha = 40

        tarefas_ordenadas = sorted(tarefas, key=lambda t: str(t.id))

        largura = margem_esquerda + max(tempo_maximo, 1) * largura_tick + 60
        altura = margem_superior + len(tarefas_ordenadas) * altura_linha + 60

        # Cria a imagem e o objeto responsável pelo desenho
        imagem = Image.new("RGB", (largura, altura), "#202020")
        desenho = ImageDraw.Draw(imagem)

        # Legenda
        desenho.text((10, 10), "Grafico de Gantt", fill="white")
        desenho.text(
            (10, 30),
            "Execucao: cor da tarefa | Pronta: P | Bloqueada: X",
            fill="white"
        )
        desenho.text(
            (10, 50),
            "Chegada: verde | Conclusao: azul | Prazo perdido: vermelho",
            fill="white"
        )

        # Desenha o eixo do tempo
        for tempo in range(tempo_maximo + 1):
            x = margem_esquerda + tempo * largura_tick

            desenho.text(
                (x - 5, margem_superior - 25),
                str(tempo),
                fill="white"
            )

            desenho.line(
                (x, margem_superior,
                 x, margem_superior + len(tarefas_ordenadas) * altura_linha),
                fill="#444444"
            )

        # Desenha as linhas das tarefas
        for indice, tarefa in enumerate(tarefas_ordenadas):
            y = margem_superior + indice * altura_linha

            desenho.text(
                (10, y + 15),
                str(tarefa.id),
                fill="white"
            )

            desenho.line(
                (margem_esquerda, y + altura_linha,
                 margem_esquerda + tempo_maximo * largura_tick,
                 y + altura_linha),
                fill="#444444"
            )

        # Desenha os estados registrados em cada tick
        for registro in historico:
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

            estado = registro["estado"]

            if estado == "Executando":
                cor = tarefa.cor
                if not cor.startswith("#"):
                    # Aceita nomes de cores e valores hexadecimais
                    try:
                        from PIL import ImageColor
                        ImageColor.getrgb(cor)
                    except ValueError:
                        cor = "#" + cor

                try:
                    desenho.rectangle(
                        (x1, y1, x2, y2),
                        fill=cor,
                        outline="white"
                    )
                except ValueError:
                    desenho.rectangle(
                        (x1, y1, x2, y2),
                        fill="#777777",
                        outline="white"
                    )

                desenho.text(
                    (x1 + 10, y1 + 8),
                    str(registro["cpu"]),
                    fill="white"
                )

            elif estado == "Pronta":
                desenho.rectangle(
                    (x1, y1, x2, y2),
                    outline="white",
                    width=2
                )
                desenho.text(
                    (x1 + 15, y1 + 8),
                    "P",
                    fill="white"
                )

            elif estado == "Bloqueada":
                desenho.rectangle(
                    (x1, y1, x2, y2),
                    fill="#555555",
                    outline="white"
                )
                desenho.line((x1 + 5, y1 + 5, x2 - 5, y2 - 5), fill="white", width=2)
                desenho.line((x1 + 5, y2 - 5, x2 - 5, y1 + 5), fill="white", width=2)

        # Desenha os eventos
        for evento in eventos:
            indice = next(
                (i for i, t in enumerate(tarefas_ordenadas)
                 if str(t.id) == str(evento["tarefa"])),
                None
            )

            if indice is None:
                continue

            x = margem_esquerda + evento["tempo"] * largura_tick
            y = margem_superior + indice * altura_linha + 8

            if evento["tipo"] == "Chegada":
                desenho.polygon(
                    [(x, y - 6), (x - 6, y + 4), (x + 6, y + 4)],
                    fill="#2ECC71"
                )

            elif evento["tipo"] == "Conclusão":
                desenho.ellipse(
                    (x - 5, y - 5, x + 5, y + 5),
                    fill="#3498DB",
                    outline="white"
                )

            elif evento["tipo"] == "Perda de prazo":
                desenho.line((x - 6, y - 6, x + 6, y + 6), fill="red", width=3)
                desenho.line((x - 6, y + 6, x + 6, y - 6), fill="red", width=3)

        # Salva o arquivo
        imagem.save(caminho, format="PNG")

