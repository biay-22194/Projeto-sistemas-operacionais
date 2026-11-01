from dataclasses import dataclass
import copy
from structs import RateMonotonic

@dataclass
class Ocorrencia:
    """
    Representa uma instância específica de uma tarefa periódica ou aperiódica.
    Cada ativação de uma tarefa gera uma nova ocorrência com prazos e durações próprios.
    """
    tarefa: object             # Referência à TCB (Task Control Block) original
    numero: int                # Número sequencial da ativação (ex: 1/10, 2/10)
    inicio: int                # Tick de relógio em que a ocorrência foi ativada
    prazo_absoluto: int        # Tick limite para conclusão (inicio + prazo_relativo)
    tempo_restante: int        # Unidades de tempo de CPU ainda necessárias para concluir
    estado: str = "Pronta"     # Estado atual da ocorrência (Pronta, Executando, Bloqueada, Concluída)
    perdeu_prazo: bool = False # Indicador de violação de prazo limite (deadline miss)


class Simulador:
    """
    Motor central de simulação do Sistema Operativo Multitarefa.
    Gere o relógio global, a alocação de CPUs, a execução do escalonador,
    o registo de eventos e o histórico para navegação no tempo (debugger).
    """

    def __init__(self, tarefas: list, algoritmo, qtde_cpus: int = 1):
        """Inicializa as estruturas de dados e prepara o estado inicial da simulação (Tick 0)."""
        self.tempo_global = 0         # Relógio global do sistema (medido em ticks)
        self.tarefas = tarefas         # Lista de TCBs registradas no sistema
        self.algoritmo = algoritmo     # Instância do algoritmo de escalonamento (RM ou EDF)
        self.ocorrencias = []          # Lista de todas as ocorrências de tarefas ativadas
        self.finalizado = False        # Flag que sinaliza o encerramento da simulação
        self.historico = []            # Registo dos estados em cada tick para o Gráfico de Gantt
        self.eventos_gantt = []        # Eventos pontuais (Chegada, Conclusão, Perda de Prazo)
        self.snapshots = []            # Histórico de estados completos para recuar/avançar ticks

        if qtde_cpus < 1:
            raise ValueError("A quantidade de CPUs deve ser maior que zero.")
        
        self.qtde_cpus = qtde_cpus

        # Estado dos processadores e contadores de uso de quantum e ociosidade
        self.cpus = [None] * self.qtde_cpus
        self.tempo_desligado = [0] * self.qtde_cpus
        self.tempo_no_quantum = [0] * self.qtde_cpus

        # Registo do número de ativações realizadas para cada tarefa
        self.ativacoes = {t.id: 0 for t in tarefas}

        # Prepara prioridades estáticas no escalonador (caso aplicável, ex: Rate Monotonic)
        self.algoritmo.preparar_tarefas(tarefas)

        # Configuração inicial dos atributos de execução das TCBs
        for tarefa in tarefas:
            tarefa.estado = "Nova"
            tarefa.tempo_execucao = 0
            tarefa.tempo_espera = 0
            tarefa.tempo_restante = tarefa.duracao

            if tarefa.periodo == 0:
                print(f"Aviso: tarefa {tarefa.id} ignorada (aperiódica).")
            elif tarefa.periodo < 0:
                raise ValueError(f"Período inválido na tarefa {tarefa.id}")

        # Salva o snapshot inicial do sistema no instante 0
        self.salvar_estado()

    def ativar_tarefas(self):
        """
        Verifica o relógio global e ativa novas ocorrências de tarefas periódicas.
        Respeita o limite do projeto de no máximo 10 ativações por tarefa.
        """
        for tarefa in self.tarefas:
            if tarefa.periodo <= 0:
                continue

            quantidade = self.ativacoes[tarefa.id]
            # Limite estipulado pelas regras do projeto (máximo de 10 execuções por tarefa periódica)
            if quantidade >= 10:
                continue

            # Cálculo do instante exato de chegada da próxima ativação
            proxima_ativacao = tarefa.ingresso + quantidade * tarefa.periodo

            # Se o tempo atual atingiu o momento de ingresso, gera a ocorrência
            if self.tempo_global >= proxima_ativacao:
                ocorrencia = Ocorrencia(
                    tarefa=tarefa,
                    numero=quantidade + 1,
                    inicio=proxima_ativacao,
                    prazo_absoluto=proxima_ativacao + tarefa.prazo,
                    tempo_restante=tarefa.duracao
                )
                self.ocorrencias.append(ocorrencia)
                self.ativacoes[tarefa.id] += 1

                # Regista o evento visual de chegada no Gantt
                self.eventos_gantt.append({
                    "tempo": self.tempo_global,
                    "tarefa": tarefa.id,
                    "ocorrencia": ocorrencia.numero,
                    "tipo": "Chegada"
                })

                print(f"  Tarefa {tarefa.id}: ativação {quantidade + 1}/10")

    def escalonar(self):
        """
        Aplica a lógica do algoritmo de escalonamento (RM ou EDF) e distribui
        as tarefas prontas prioritárias entre as CPUs disponíveis, aplicando critérios de desempate.
        """
        # Seleciona apenas as ocorrências que estão aptas a executar
        aptas = [
            o for o in self.ocorrencias
            if o.estado in ("Pronta", "Executando")
        ]

        selecionadas = []

        # Ocorrências que já se encontravam a executar em alguma CPU no tick anterior
        ocorrencias_em_execucao = [
            o for o in self.cpus if o is not None
        ]

        # Seleção gulosa das ocorrências de maior prioridade até preencher as CPUs
        while aptas and len(selecionadas) < self.qtde_cpus:

            def chave_selecao(o):
                """
                Define a prioridade principal e a hierarquia de desempate:
                1. Prioridade do Algoritmo (Período em RM ou Prazo Absoluto em EDF)
                2. Manutenção da CPU (prefere manter a tarefa que já executava para evitar troca de contexto)
                3. Menor Prazo Absoluto
                4. Menor Instante de Ingresso
                5. Menor Duração
                6. Ordem Alfabética do ID
                """
                if isinstance(self.algoritmo, RateMonotonic):
                    prioridade = o.tarefa.periodo
                else:
                    prioridade = o.prazo_absoluto

                ja_executando = (
                    0 if any(o is atual for atual in ocorrencias_em_execucao)
                    else 1
                )

                return (
                    prioridade,
                    ja_executando,
                    o.prazo_absoluto,
                    o.tarefa.ingresso,
                    o.tarefa.duracao,
                    str(o.tarefa.id)
                )

            # Escolhe a ocorrência com menor valor na chave de seleção (maior prioridade)
            proxima = min(aptas, key=chave_selecao)

            selecionadas.append(proxima)
            aptas.remove(proxima)
        
        # Mapeamento e distribuição das tarefas selecionadas entre os núcleos de CPU
        novas_cpus = [None] * self.qtde_cpus
        
        # 1. Tenta manter a tarefa na mesma CPU onde já estava executando (afinidade)
        for i in range(self.qtde_cpus):
            ocorrencia_atual = self.cpus[i]
            if any(o is ocorrencia_atual for o in selecionadas):
                novas_cpus[i] = ocorrencia_atual
                selecionadas = [
                    o for o in selecionadas
                    if o is not ocorrencia_atual
                ]
        
        # 2. Preenche os núcleos ociosos restantes com as tarefas selecionadas
        for i in range(self.qtde_cpus):
            if novas_cpus[i] is None and selecionadas:
                novas_cpus[i] = selecionadas.pop(0)

        # Atualiza os estados das ocorrências
        for ocorrencia in self.ocorrencias:
            if ocorrencia.estado == "Executando":
                ocorrencia.estado = "Pronta"

        for ocorrencia in novas_cpus:
            if ocorrencia is not None:
                ocorrencia.estado = "Executando"

        # Reinicia o contador de quantum caso a CPU tenha trocado de tarefa
        for i in range(self.qtde_cpus):
            tarefa_anterior = self.cpus[i]
            nova_tarefa = novas_cpus[i]

            if tarefa_anterior is not nova_tarefa:
                self.tempo_no_quantum[i] = 0

        self.cpus = novas_cpus

    def executar(self):
        """
        Simula a passagem de 1 tick de relógio de processamento em cada CPU.
        Atualiza os tempos de execução, trata conclusão e esgotamento do quantum.
        """
        for i in range(self.qtde_cpus):
            ocorrencia = self.cpus[i]

            # Processamento de CPU Ociosa/Desligada
            if ocorrencia is None:
                self.tempo_desligado[i] += 1
                self.tempo_no_quantum[i] = 0
                print(f"CPU {i}: ociosa")
                continue

            # Processamento de CPU Ativa
            print(f"CPU {i}: executando tarefa {ocorrencia.tarefa.id}")

            # Regista a execução no histórico de estados do tick atual
            self.historico.append({
                "tempo": self.tempo_global,
                "cpu": i,
                "tarefa": ocorrencia.tarefa.id,
                "ocorrencia": ocorrencia.numero,
                "estado": "Executando"
            })

            ocorrencia.tempo_restante -= 1
            ocorrencia.tarefa.tempo_execucao += 1
            self.tempo_no_quantum[i] += 1

            # Tratamento de Conclusão da Ocorrência
            if ocorrencia.tempo_restante <= 0:
                ocorrencia.estado = "Concluída"
                self.eventos_gantt.append({
                    "tempo": self.tempo_global + 1,
                    "tarefa": ocorrencia.tarefa.id,
                    "ocorrencia": ocorrencia.numero,
                    "tipo": "Conclusão"
                })

                print(f"CPU {i}: tarefa {ocorrencia.tarefa.id} concluída")

                self.cpus[i] = None
                self.tempo_no_quantum[i] = 0

            # Tratamento de Esgotamento de Quantum (Preempção por tempo)
            elif (
                self.algoritmo.quantum is not None
                and self.tempo_no_quantum[i] >= self.algoritmo.quantum
            ):
                ocorrencia.estado = "Pronta"
                print(f"CPU {i}: quantum esgotado para {ocorrencia.tarefa.id}")

                self.cpus[i] = None
                self.tempo_no_quantum[i] = 0

    def atualizar_estados(self):
        """
        Consolida o estado geral de cada TCB com base no estado das suas ocorrências ativas.
        Permite que a tabela de tarefas exiba o estado macro atual (Ex: Executando, Pronta, Concluída).
        """
        for tarefa in self.tarefas:
            if tarefa.periodo == 0:
                tarefa.estado = "Ignorada"
                continue

            pendentes = [
                o for o in self.ocorrencias
                if o.tarefa is tarefa and o.estado != "Concluída"
            ]

            tarefa.tempo_restante = sum(o.tempo_restante for o in pendentes)

            if pendentes:
                if any(o.estado == "Executando" for o in pendentes):
                    tarefa.estado = "Executando"
                elif any(o.estado == "Pronta" for o in pendentes):
                    tarefa.estado = "Pronta"
                elif all(o.estado == "Bloqueada" for o in pendentes):
                    tarefa.estado = "Bloqueada"
            elif self.ativacoes[tarefa.id] == 10:
                tarefa.estado = "Concluída"
            else:
                tarefa.estado = "Nova"

    def salvar_estado(self):
        """
        Cria uma cópia profunda (deep copy) do estado atual do simulador.
        Utilizado para permitir a funcionalidade de recuar/avançar no tempo (debugger).
        """
        estado_atual = copy.deepcopy({
            "tempo_global": self.tempo_global,
            "tarefas": self.tarefas,
            "ocorrencias": self.ocorrencias,
            "finalizado": self.finalizado,
            "historico": self.historico,
            "eventos_gantt": self.eventos_gantt,
            "cpus": self.cpus,
            "tempo_desligado": self.tempo_desligado,
            "tempo_no_quantum": self.tempo_no_quantum,
            "ativacoes": self.ativacoes
        })
        
        # Se a simulação recuou e o utilizador avançou gerando um novo futuro, descarta o histórico posterior
        if len(self.snapshots) > self.tempo_global:
            self.snapshots = self.snapshots[:self.tempo_global]
            
        self.snapshots.append(estado_atual)

    def carregar_estado(self, tempo):
        """Restaura todas as variáveis da simulação para o estado guardado num tick específico."""
        if 0 <= tempo < len(self.snapshots):
            estado = copy.deepcopy(self.snapshots[tempo])
            self.tempo_global = estado["tempo_global"]
            self.tarefas = estado["tarefas"]
            self.ocorrencias = estado["ocorrencias"]
            self.finalizado = estado["finalizado"]
            self.historico = estado["historico"]
            self.eventos_gantt = estado["eventos_gantt"]
            self.cpus = estado["cpus"]
            self.tempo_desligado = estado["tempo_desligado"]
            self.tempo_no_quantum = estado["tempo_no_quantum"]
            self.ativacoes = estado["ativacoes"]

    def verificar_prazos(self):
        """Verifica se alguma ocorrência em aberto ultrapassou o seu prazo limite absoluto (deadline)."""
        for ocorrencia in self.ocorrencias:
            if (
                ocorrencia.estado != "Concluída"
                and not ocorrencia.perdeu_prazo
                and self.tempo_global >= ocorrencia.prazo_absoluto
            ):
                ocorrencia.perdeu_prazo = True
                self.eventos_gantt.append({
                    "tempo": self.tempo_global,
                    "tarefa": ocorrencia.tarefa.id,
                    "ocorrencia": ocorrencia.numero,
                    "tipo": "Perda de prazo"
                })               
                
                print(f"  PRAZO PERDIDO: tarefa {ocorrencia.tarefa.id}, ativação {ocorrencia.numero}")

    def verificar_fim(self):
        """Avalia se todas as tarefas do sistema foram concluídas para encerrar a simulação."""
        todas_concluidas = all(getattr(tarefa, 'estado', '') == "Concluída" for tarefa in self.tarefas)
        
        if todas_concluidas and self.tarefas:
            self.finalizado = True
            print("\nSimulação finalizada!")

            for i in range(self.qtde_cpus):
                print(
                    f"CPU {i}: "
                    f"{self.tempo_desligado[i]} ticks ociosos"
                )

    def avancar_tick(self):
        """
        Executa a sequência completa de passos de um ciclo de relógio (Tick):
        1. Ativação de novas instâncias de tarefas.
        2. Escalonamento e alocação de CPUs.
        3. Registo de tarefas prontas/bloqueadas no histórico.
        4. Processamento da execução nas CPUs.
        5. Incremento do relógio e verificação de prazos/término.
        6. Gravação do snapshot para o histórico de navegação temporal.
        """
        if self.finalizado:
            print("A simulação já terminou.")
            return

        print(f"\n--- Tick {self.tempo_global} ---")

        self.ativar_tarefas()
        self.escalonar()

        # Guarda o registo das tarefas que permaneceram em espera/bloqueio neste tick
        for ocorrencia in self.ocorrencias:
            if ocorrencia.estado in ("Pronta", "Bloqueada"):
                self.historico.append({
                    "tempo": self.tempo_global,
                    "cpu": None,
                    "tarefa": ocorrencia.tarefa.id,
                    "ocorrencia": ocorrencia.numero,
                    "estado": ocorrencia.estado
                })

        self.executar()
        self.tempo_global += 1

        self.verificar_prazos()
        self.atualizar_estados()
        self.verificar_fim()
        self.salvar_estado() # Grava o estado atualizado no histórico de snapshots