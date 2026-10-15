from dataclasses import dataclass

@dataclass
class Ocorrencia:
    tarefa: object
    numero: int
    inicio: int
    prazo_absoluto: int
    tempo_restante: int
    estado: str = "Pronta"
    perdeu_prazo: bool = False


class Simulador:

    def __init__(self, tarefas: list, algoritmo):
        self.tempo_global = 0
        self.tarefas = tarefas
        self.algoritmo = algoritmo
        self.ocorrencias = []
        self.finalizado = False
        
        # Gestão de 1 CPU
        self.cpu = None
        self.tempo_desligado = 0  # Registra a ociosidade do processador
        self.tempo_no_quantum = 0

        self.ativacoes = {t.id: 0 for t in tarefas}

        # Prepara prioridades estáticas se necessário
        self.algoritmo.preparar_tarefas(tarefas)

        for tarefa in tarefas:
            tarefa.estado = "Nova"
            tarefa.tempo_execucao = 0
            tarefa.tempo_espera = 0
            tarefa.tempo_restante = tarefa.duracao

            if tarefa.periodo == 0:
                print(f"Aviso: tarefa {tarefa.id} ignorada (aperiódica).")
            elif tarefa.periodo < 0:
                raise ValueError(f"Período inválido na tarefa {tarefa.id}")

    def ativar_tarefas(self):
        for tarefa in self.tarefas:
            if tarefa.periodo <= 0:
                continue

            quantidade = self.ativacoes[tarefa.id]
            if quantidade >= 10:
                continue

            proxima_ativacao = tarefa.ingresso + quantidade * tarefa.periodo

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
                print(f"  Tarefa {tarefa.id}: ativação {quantidade + 1}/10")

    def escalonar(self):
        # Seleciona ocorrências em estado Pronta ou Executando
        aptas = [
            o for o in self.ocorrencias
            if o.estado in ("Pronta", "Executando")
        ]

        if not aptas:
            if self.cpu is not None and self.cpu.estado == "Executando":
                self.cpu.estado = "Pronta"
            self.cpu = None
            self.tempo_no_quantum = 0
            return

        # Pede ao algoritmo a próxima tarefa respeitando os 5 critérios de desempate
        proxima = self.algoritmo.selecionar_proxima(aptas, self.cpu)

        # Trata preempção / troca de contexto
        if self.cpu != proxima:
            if self.cpu is not None and self.cpu.estado == "Executando":
                self.cpu.estado = "Pronta"
            self.tempo_no_quantum = 0

        self.cpu = proxima
        self.cpu.estado = "Executando"

    def executar(self):
        if self.cpu is None:
            self.tempo_desligado += 1
            print(f"  CPU desligada: nenhuma tarefa pronta. (Ociosa por {self.tempo_desligado} ticks)")
            self.tempo_no_quantum = 0
            return

        ocorrencia = self.cpu
        print(f"  CPU executando tarefa {ocorrencia.tarefa.id} (ativação {ocorrencia.numero})")

        ocorrencia.tempo_restante -= 1
        ocorrencia.tarefa.tempo_execucao += 1
        self.tempo_no_quantum += 1

        # Caso A: Conclusão da ocorrência
        if ocorrencia.tempo_restante <= 0:
            ocorrencia.estado = "Concluída"
            print(f"  Tarefa {ocorrencia.tarefa.id}: ativação {ocorrencia.numero} concluída.")
            self.tempo_no_quantum = 0
            self.cpu = None

        # Caso B: Esgotamento do quantum (se houver quantum definido)
        elif self.algoritmo.quantum is not None and self.tempo_no_quantum >= self.algoritmo.quantum:
            ocorrencia.estado = "Pronta"
            print(f"  Quantum de {self.algoritmo.quantum} ticks atingido para tarefa {ocorrencia.tarefa.id}.")
            self.tempo_no_quantum = 0
            self.cpu = None

    def atualizar_estados(self):
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
                else:
                    tarefa.estado = "Pronta"
            elif self.ativacoes[tarefa.id] == 10:
                tarefa.estado = "Concluída"
            else:
                tarefa.estado = "Nova"

    def verificar_prazos(self):
        for ocorrencia in self.ocorrencias:
            if (
                ocorrencia.estado != "Concluída"
                and not ocorrencia.perdeu_prazo
                and self.tempo_global >= ocorrencia.prazo_absoluto
            ):
                ocorrencia.perdeu_prazo = True
                print(f"  PRAZO PERDIDO: tarefa {ocorrencia.tarefa.id}, ativação {ocorrencia.numero}")

    def verificar_fim(self):
        validas = [t for t in self.tarefas if t.periodo > 0]
        todas_ativadas = all(self.ativacoes[t.id] == 10 for t in validas)
        todas_concluidas = all(o.estado == "Concluída" for o in self.ocorrencias)

        if todas_ativadas and todas_concluidas:
            self.finalizado = True
            print(f"\nSimulação finalizada! Tempo total ocioso da CPU: {self.tempo_desligado} ticks.")

    def avancar_tick(self):
        if self.finalizado:
            print("A simulação já terminou.")
            return

        print(f"\n--- Tick {self.tempo_global} ---")

        self.ativar_tarefas()
        self.escalonar()
        self.executar()

        self.tempo_global += 1

        self.verificar_prazos()
        self.atualizar_estados()
        self.verificar_fim()