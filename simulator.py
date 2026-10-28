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

    def __init__(self, tarefas: list, algoritmo, qtde_cpus: int = 1):
        self.tempo_global = 0
        self.tarefas = tarefas
        self.algoritmo = algoritmo
        self.ocorrencias = []
        self.finalizado = False
        self.historico = []               #armazena os estados durante cada tick
        self.eventos_gantt = []           #armazena acontecimentos pontuais

        if qtde_cpus < 1:
            raise ValueError("A quantidade de CPUs deve ser maior que zero.")
        
        self.qtde_cpus = qtde_cpus

        self.cpus = [None] * self.qtde_cpus
        self.tempo_desligado = [0] * self.qtde_cpus
        self.tempo_no_quantum = [0] * self.qtde_cpus

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

                self.eventos_gantt.append({                  #quando uma nova ocorrência é ativada, registramos sua chegada
                    "tempo": self.tempo_global,
                    "tarefa": tarefa.id,
                    "ocorrencia": ocorrencia.numero,
                    "tipo": "Chegada"
                })

                print(f"  Tarefa {tarefa.id}: ativação {quantidade + 1}/10")

    def escalonar(self):

        aptas = [
            o for o in self.ocorrencias
            if o.estado in ("Pronta", "Executando")
        ]

        # Seleciona as ocorrências prioritárias
        selecionadas = []
        
        while aptas and len(selecionadas) < self.qtde_cpus:
        
            proxima = self.algoritmo.selecionar_proxima(
                aptas,
                None
            )
        
            selecionadas.append(proxima)
            aptas.remove(proxima)
        
        # Prepara a distribuição entre as CPUs
        novas_cpus = [None] * self.qtde_cpus
        
        # Mantém as ocorrências nas CPUs onde já estavam
        for i in range(self.qtde_cpus):
        
            ocorrencia_atual = self.cpus[i]
        
            if any(o is ocorrencia_atual for o in selecionadas):
                novas_cpus[i] = ocorrencia_atual
                selecionadas = [
                    o for o in selecionadas
                    if o is not ocorrencia_atual
                ]
        
        # Distribui as ocorrências restantes
        for i in range(self.qtde_cpus):
        
            if novas_cpus[i] is None and selecionadas:
                novas_cpus[i] = selecionadas.pop(0)

        for ocorrencia in self.ocorrencias:
            if ocorrencia.estado == "Executando":
                ocorrencia.estado = "Pronta"

        for ocorrencia in novas_cpus:
            if ocorrencia is not None:
                ocorrencia.estado = "Executando"

        # Verifica se alguma CPU mudou de tarefa
        for i in range(self.qtde_cpus):

            tarefa_anterior = self.cpus[i]
            nova_tarefa = novas_cpus[i]

            if tarefa_anterior is not nova_tarefa:
                self.tempo_no_quantum[i] = 0

        # Atualiza as CPUs
        self.cpus = novas_cpus

    def executar(self):

        for i in range(self.qtde_cpus):

            ocorrencia = self.cpus[i]

            # CPU ociosa
            if ocorrencia is None:
                self.tempo_desligado[i] += 1
                self.tempo_no_quantum[i] = 0

                print(f"CPU {i}: ociosa")
                continue

            # CPU executando uma tarefa
            print(
                f"CPU {i}: executando tarefa "
                f"{ocorrencia.tarefa.id}"
            )

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

            # Tarefa concluída
            if ocorrencia.tempo_restante <= 0:

                ocorrencia.estado = "Concluída"
                self.eventos_gantt.append({
               "tempo": self.tempo_global + 1,
               "tarefa": ocorrencia.tarefa.id,
               "ocorrencia": ocorrencia.numero,
               "tipo": "Conclusão"
               })

                print(
                    f"CPU {i}: tarefa "
                    f"{ocorrencia.tarefa.id} concluída"
                )

                self.cpus[i] = None
                self.tempo_no_quantum[i] = 0

            # Quantum esgotado
            elif (
                self.algoritmo.quantum is not None
                and self.tempo_no_quantum[i] >= self.algoritmo.quantum
            ):

                ocorrencia.estado = "Pronta"

                print(
                    f"CPU {i}: quantum esgotado para "
                    f"{ocorrencia.tarefa.id}"
                )

                self.cpus[i] = None
                self.tempo_no_quantum[i] = 0
      

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

                elif any(o.estado == "Pronta" for o in pendentes):
                    tarefa.estado = "Pronta"

                elif all(o.estado == "Bloqueada" for o in pendentes):
                    tarefa.estado = "Bloqueada"
             
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
                self.eventos_gantt.append({
               "tempo": self.tempo_global,
               "tarefa": ocorrencia.tarefa.id,
               "ocorrencia": ocorrencia.numero,
               "tipo": "Perda de prazo"
                })               
                
                print(f"  PRAZO PERDIDO: tarefa {ocorrencia.tarefa.id}, ativação {ocorrencia.numero}")

    def verificar_fim(self):
        validas = [t for t in self.tarefas if t.periodo > 0]

        todas_ativadas = all(
            self.ativacoes[t.id] == 10 for t in validas
        )

        todas_concluidas = all(
            o.estado == "Concluída" for o in self.ocorrencias
        )

        if todas_ativadas and todas_concluidas:
            self.finalizado = True

            print("\nSimulação finalizada!")

            for i in range(self.qtde_cpus):
                print(
                    f"CPU {i}: "
                    f"{self.tempo_desligado[i]} ticks ociosos"
                )

    def avancar_tick(self):
        if self.finalizado:
            print("A simulação já terminou.")
            return

        print(f"\n--- Tick {self.tempo_global} ---")

        self.ativar_tarefas()
        self.escalonar()
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