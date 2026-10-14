# classe responsável por controlar a simulação
from dataclasses import dataclass


@dataclass
class Ocorrencia:
    # Cada ativação periódica gera uma ocorrência independente
    tarefa: object
    numero: int
    inicio: int
    prazo_absoluto: int
    tempo_restante: int
    estado: str = "Pronta"
    perdeu_prazo: bool = False


class Simulador:

    def __init__(self, tarefas):
        self.tempo_global = 0
        self.tarefas = tarefas
        self.ocorrencias = []
        self.finalizado = False

        # Escalonador provisório: apenas uma CPU
        self.cpu = None

        # Contagem de ativações por tarefa
        self.ativacoes = {t.id: 0 for t in tarefas}

        # Tarefas aperiódicas não participam do Projeto A
        for tarefa in tarefas:
            tarefa.estado = "Nova"
            tarefa.tempo_execucao = 0
            tarefa.tempo_espera = 0
            tarefa.tempo_restante = tarefa.duracao

            if tarefa.periodo == 0:
                print(f"Aviso: tarefa {tarefa.id} ignorada (aperiódica).")
            elif tarefa.periodo < 0:
                raise ValueError(
                    f"Período inválido na tarefa {tarefa.id}"
                )

    def ativar_tarefas(self):
        for tarefa in self.tarefas:

            if tarefa.periodo == 0:
                continue

            quantidade = self.ativacoes[tarefa.id]

            if quantidade >= 10:
                continue

            proxima_ativacao = (
                tarefa.ingresso + quantidade * tarefa.periodo
            )

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

                print(
                    f"  Tarefa {tarefa.id}: "
                    f"ativação {quantidade + 1}/10"
                )

    def escalonar(self):
        # Provisório: seleciona a primeira ocorrência pronta
        prontas = [
            o for o in self.ocorrencias
            if o.estado == "Pronta"
        ]

        self.cpu = prontas[0] if prontas else None

        if self.cpu:
            self.cpu.estado = "Executando"

    def executar(self):
        if self.cpu is None:
            print("  CPU desligada: nenhuma tarefa pronta.")
            return

        ocorrencia = self.cpu

        print(
            f"  CPU executando tarefa {ocorrencia.tarefa.id} "
            f"(ativação {ocorrencia.numero})"
        )

        ocorrencia.tempo_restante -= 1
        ocorrencia.tarefa.tempo_execucao += 1

        if ocorrencia.tempo_restante <= 0:
            ocorrencia.estado = "Concluída"

            print(
                f"  Tarefa {ocorrencia.tarefa.id}: "
                f"ativação {ocorrencia.numero} concluída."
            )
        else:
            ocorrencia.estado = "Pronta"

        self.cpu = None

    def atualizar_estados(self):
        for tarefa in self.tarefas:
            if tarefa.periodo == 0:
                tarefa.estado = "Ignorada"
                continue

            pendentes = [
                o for o in self.ocorrencias
                if o.tarefa is tarefa
                and o.estado != "Concluída"
            ]

            tarefa.tempo_restante = sum(
                o.tempo_restante for o in pendentes
            )

            if pendentes:
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

                print(
                    f"  PRAZO PERDIDO: tarefa "
                    f"{ocorrencia.tarefa.id}, "
                    f"ativação {ocorrencia.numero}"
                )

    def verificar_fim(self):
        validas = [
            t for t in self.tarefas if t.periodo > 0
        ]

        todas_ativadas = all(
            self.ativacoes[t.id] == 10 for t in validas
        )

        todas_concluidas = all(
            o.estado == "Concluída"
            for o in self.ocorrencias
        )

        if todas_ativadas and todas_concluidas:
            self.finalizado = True
            print("\nSimulação finalizada!")

    def avancar_tick(self):
        if self.finalizado:
            print("A simulação já terminou.")
            return

        print(f"\n--- Tick {self.tempo_global} ---")

        self.ativar_tarefas()
        self.escalonar()
        self.executar()

        # Avança o relógio após executar o intervalo atual
        self.tempo_global += 1

        self.verificar_prazos()
        self.atualizar_estados()
        self.verificar_fim()