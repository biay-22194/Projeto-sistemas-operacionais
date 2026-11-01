from dataclasses import dataclass, field
import random

@dataclass
class TCB:
    """
    Estrutura de dados TCB (Task Control Block).
    Armazena todos os metadados, características temporais e métricas de execução
    de uma tarefa individual dentro do simulador do Sistema Operativo.
    """
    id: str                   # Identificador único da tarefa (ex: "T1", "A")
    cor: str                  # Cor representativa na interface visual (hexadecimal ou nome)
    ingresso: int             # Instante de tempo (tick) em que a tarefa entra no sistema
    duracao: int              # Tempo total de processamento necessário por execução (C)
    periodo: int              # Intervalo de tempo entre reativações (T). Se 0, a tarefa é aperiódica
    prazo: int                # Prazo limite relativo de execução / deadline (D)
    lista_eventos: list       # Lista de eventos específicos associados à tarefa
    prioridade: int = 0       # Prioridade estática calculada para algoritmos como Rate Monotonic
    estado: str = "Nova"      # Estado corrente da tarefa (Nova, Pronta, Executando, Bloqueada, Concluída)
    
    # Campos de controlo de métricas e tempo remaining
    tempo_restante: int = field(init=False)  # Unidades de tempo de CPU ainda necessárias
    tempo_espera: int = 0                    # Acumulador do tempo passado na fila de prontos
    tempo_execucao: int = 0                  # Acumulador do tempo efetivamente processado na CPU

    def __post_init__(self):
        """Inicializa o tempo restante de processamento com o valor total da duração inicial."""
        self.tempo_restante = int(self.duracao)


class RateMonotonic:
    """
    Algoritmo de Escalonamento Rate Monotonic (RM) preemptivo.
    Aplica uma política de prioridade estática baseada no período da tarefa:
    quanto menor o período, maior é a prioridade atribuída.
    """
    def __init__(self, quantum: int = None):
        """Inicializa o escalonador RM, guardando opcionalmente o valor do quantum de tempo."""
        self.quantum = quantum

    def preparar_tarefas(self, tcbs: list):
        """
        Atribui prioridade estática às tarefas periódicas com base no seu período.
        Em RM, prioridade = período (valores menores representam maior prioridade na ordenação).
        """
        for tcb in tcbs:
            if tcb.periodo > 0:
                tcb.prioridade = tcb.periodo

    def _obter_chave(self, ocorrencia, cpu_atual):
        """
        Gera a tupla de ordenação e desempate estipulada pelo Requisito 4.3:
        0. Prioridade estática do algoritmo RM (menor período = maior prioridade).
        1. Manutenção na CPU (prefere a ocorrência que já estava em execução na CPU para minimizar trocas de contexto).
        2. Menor prazo absoluto limite (deadline).
        3. Menor instante de ingresso no sistema.
        4. Menor duração total da tarefa.
        5. Sorteio aleatório (random) como último recurso de desempate.
        """
        # Define 0 se a ocorrência já executava na CPU atual; caso contrário, define 1
        ja_executando = 0 if (cpu_atual is not None and ocorrencia == cpu_atual) else 1

        return (
            ocorrencia.tarefa.prioridade,  # Prioridade estática RM (baseada no período)
            ja_executando,                 # (1) Continuidade de execução na CPU
            ocorrencia.prazo_absoluto,     # (2) Prazo limite absoluto
            ocorrencia.tarefa.ingresso,    # (3) Instante de ingresso
            ocorrencia.tarefa.duracao,     # (4) Duração total
            random.random()                # (5) Sorteio aleatório
        )

    def selecionar_proxima(self, ocorrencias_aptas: list, cpu_atual):
        """
        Seleciona a ocorrência de maior prioridade de entre a lista de tarefas aptas a executar.
        Retorna None caso a fila esteja vazia.
        """
        if not ocorrencias_aptas:
            return None
        return min(ocorrencias_aptas, key=lambda o: self._obter_chave(o, cpu_atual))


class EarliestDeadlineFirst:
    """
    Algoritmo de Escalonamento Earliest Deadline First (EDF) preemptivo.
    Aplica uma política de prioridade dinâmica baseada no prazo limite absoluto (deadline):
    a ocorrência mais próxima de atingir a sua deadline ganha prioridade de execução.
    """
    def __init__(self, quantum: int = None):
        """Inicializa o escalonador EDF, guardando opcionalmente o valor do quantum de tempo."""
        self.quantum = quantum

    def preparar_tarefas(self, tcbs: list):
        """
        Como o EDF utiliza prioridades dinâmicas avaliadas em tempo de execução
        (prazo absoluto de cada ocorrência), não necessita de pré-processamento estático.
        """
        pass

    def _obter_chave(self, ocorrencia, cpu_atual):
        """
        Gera a tupla de ordenação e desempate para o algoritmo EDF (Requisito 4.3):
        0. Menor prazo absoluto limite (deadline mais próxima = maior prioridade dinâmica).
        1. Manutenção na CPU (evita troca de contexto desnecessária).
        2. Menor prazo relativo limite.
        3. Menor instante de ingresso.
        4. Menor duração total da tarefa.
        5. Sorteio aleatório (random).
        """
        ja_executando = 0 if (cpu_atual is not None and ocorrencia == cpu_atual) else 1

        return (
            ocorrencia.prazo_absoluto,     # Prioridade dinâmica EDF (deadline mais próxima)
            ja_executando,                 # (1) Continuidade de execução na CPU
            ocorrencia.prazo_absoluto,     # (2) Prazo limite
            ocorrencia.tarefa.ingresso,    # (3) Instante de ingresso
            ocorrencia.tarefa.duracao,     # (4) Duração total
            random.random()                # (5) Sorteio aleatório
        )

    def selecionar_proxima(self, ocorrencias_aptas: list, cpu_atual):
        """
        Seleciona a ocorrência com o prazo absoluto mais urgente de entre as tarefas aptas.
        Retorna None caso a fila esteja vazia.
        """
        if not ocorrencias_aptas:
            return None
        return min(ocorrencias_aptas, key=lambda o: self._obter_chave(o, cpu_atual))