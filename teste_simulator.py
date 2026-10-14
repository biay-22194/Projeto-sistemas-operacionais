from structs import TCB
from simulator import Simulador

tarefa1 = TCB(
    id="1",
    cor="FF0000",
    ingresso=0,
    duracao=2,
    periodo=5,
    prazo=5,
    lista_eventos=[]
)

tarefa2 = TCB(
    id="2",
    cor="00FF00",
    ingresso=1,
    duracao=1,
    periodo=4,
    prazo=4,
    lista_eventos=[]
)

simulador = Simulador([tarefa1, tarefa2])

while not simulador.finalizado:
    simulador.avancar_tick()

print("\nTempo final:", simulador.tempo_global)
print("Ativações:", simulador.ativacoes)
print("Estado T1:", tarefa1.estado)
print("Estado T2:", tarefa2.estado)