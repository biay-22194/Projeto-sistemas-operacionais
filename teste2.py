from structs import TCB, RateMonotonic, EarliestDeadlineFirst
from simulator import Simulador

tarefas = [
    TCB(id="A", cor="red", ingresso=0, duracao=2, periodo=5, prazo=5, lista_eventos=[]),
    TCB(id="B", cor="blue", ingresso=0, duracao=3, periodo=10, prazo=10, lista_eventos=[]),
]

# Para usar EDF com quantum de 2 ticks:
algoritmo_edf = EarliestDeadlineFirst(quantum=2)
simulador = Simulador(tarefas=tarefas, algoritmo=algoritmo_edf)

# Para rodar a simulação passo a passo:
for _ in range(15):
    simulador.avancar_tick()