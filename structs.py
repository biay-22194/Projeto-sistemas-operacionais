
from dataclasses import dataclass, field

@dataclass
class TCB:
    id: str
    cor: str
    ingresso: int
    duracao: int
    periodo: int
    prazo: int
    lista_eventos: list 
    
    # Atributos de controle do SO - que mudam durante a simulação 
    estado: str = "Nova"
    tempo_restante: int = field(init=False)
    tempo_espera: int = 0
    tempo_execucao: int = 0

    def __post_init__(self):
        # Roda automaticamente logo após a criação do objeto
        self.tempo_restante = int(self.duracao)