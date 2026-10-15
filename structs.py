from dataclasses import dataclass, field
import random

@dataclass
class TCB:
    id: str
    cor: str
    ingresso: int
    duracao: int
    periodo: int
    prazo: int
    lista_eventos: list
    prioridade: int = 0
    estado: str = "Nova"
    tempo_restante: int = field(init=False)
    tempo_espera: int = 0
    tempo_execucao: int = 0

    def __post_init__(self):
        self.tempo_restante = int(self.duracao)


class RateMonotonic:
    def __init__(self, quantum: int = None):
        self.quantum = quantum

    def preparar_tarefas(self, tcbs: list):
        """Atribui prioridade estática baseada no menor período (RM)."""
        validas = [t for t in tcbs if t.periodo > 0]
        validas.sort(key=lambda t: (t.periodo, t.ingresso))
        for idx, tcb in enumerate(validas, start=1):
            tcb.prioridade = idx

    def _obter_chave(self, ocorrencia, cpu_atual):
        """
        Retorna a tupla de ordenação do RM com os 5 critérios de desempate (Requisito 4.3):
        0. Prioridade RM (menor período = maior prioridade)
        1. Tarefa já executando na CPU (evitar troca de contexto)
        2. Menor prazo da tarefa (deadline)
        3. Menor instante de ingresso
        4. Menor duração da tarefa
        5. Sorteio (random)
        """
        ja_executando = 0 if (cpu_atual is not None and ocorrencia == cpu_atual) else 1

        return (
            ocorrencia.tarefa.prioridade,  # Prioridade estática RM
            ja_executando,                 # (1) Manter tarefa atual na CPU
            ocorrencia.prazo_absoluto,     # (2) Prazo limite
            ocorrencia.tarefa.ingresso,    # (3) Instante de ingresso
            ocorrencia.tarefa.duracao,     # (4) Duração
            random.random()                # (5) Sorteio
        )

    def selecionar_proxima(self, ocorrencias_aptas: list, cpu_atual):
        if not ocorrencias_aptas:
            return None
        return min(ocorrencias_aptas, key=lambda o: self._obter_chave(o, cpu_atual))


class EarliestDeadlineFirst:
    def __init__(self, quantum: int = None):
        self.quantum = quantum

    def preparar_tarefas(self, tcbs: list):
        """EDF é dinâmico, não necessita de prioridades estáticas prévias."""
        pass

    def _obter_chave(self, ocorrencia, cpu_atual):
        """
        Retorna a tupla de ordenação do EDF com os 5 critérios de desempate (Requisito 4.3):
        0. Menor deadline absoluta (EDF)
        1. Tarefa já executando na CPU (evitar troca de contexto)
        2. Menor prazo da tarefa
        3. Menor instante de ingresso
        4. Menor duração da tarefa
        5. Sorteio (random)
        """
        ja_executando = 0 if (cpu_atual is not None and ocorrencia == cpu_atual) else 1

        return (
            ocorrencia.prazo_absoluto,     # Prioridade dinâmica EDF
            ja_executando,                 # (1) Manter tarefa atual na CPU
            ocorrencia.prazo_absoluto,     # (2) Prazo limite
            ocorrencia.tarefa.ingresso,    # (3) Instante de ingresso
            ocorrencia.tarefa.duracao,     # (4) Duração
            random.random()                # (5) Sorteio
        )

    def selecionar_proxima(self, ocorrencias_aptas: list, cpu_atual):
        if not ocorrencias_aptas:
            return None
        return min(ocorrencias_aptas, key=lambda o: self._obter_chave(o, cpu_atual))