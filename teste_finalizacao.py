from structs import TCB, RateMonotonic
from simulator import Simulador

# Cria uma tarefa simples
tarefa = TCB(
    id="A",
    cor="red",
    ingresso=0,
    duracao=1,
    periodo=3,
    prazo=3,
    lista_eventos=[]
)

# Cria o algoritmo de escalonamento
algoritmo = RateMonotonic(quantum=2)

# Cria o simulador com duas CPUs
simulador = Simulador(
    tarefas=[tarefa],
    algoritmo=algoritmo,
    qtde_cpus=2
)

# Executa até a simulação terminar
while not simulador.finalizado:
    simulador.avancar_tick()

print("\nRESULTADO FINAL")
print("Tempo total:", simulador.tempo_global)
print("Ativações:", simulador.ativacoes)
print("Ociosidade das CPUs:", simulador.tempo_desligado)