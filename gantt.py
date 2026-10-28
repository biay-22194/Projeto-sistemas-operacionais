import tkinter as tk

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
        margem_superior = 40
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