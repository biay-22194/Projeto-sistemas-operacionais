Dia 1: estrutura da TCB, pega arquivos txt com as configurações e os salva. OBS: não foi feita a visualização das tarefas na interface (melhor fazer depois).

Dia 2 — Motor da Simulação

Criei o arquivo simulator.py, responsável por controlar a execução das tarefas.

Implementei o relógio global, que avança em ticks.

Implementei a ativação periódica das tarefas, com limite de 10 ativações por tarefa.

Adicionei o controle dos estados, do tempo restante de execução e da verificação de prazos (deadlines).

Criei um escalonador provisório que seleciona a primeira tarefa disponível.

Integrei o simulador à interface gráfica, adicionando o botão Avançar Tick e o contador de tempo.

Status: a implementação está pronta e a interface abre normalmente, mas ainda falta testar a execução com um arquivo de configuração.

Dia 3 - implementei os métodos de escalonamento rate monotonic e earliest deadline first, tive que mudar no simulador na parte de quantum. Não fiz a mudança de selecionar o algoritmo sem alterar o motor da simulação, vou fazer no meu próximo dia.


Dia 4 — Múltiplas CPUs
Implementei o suporte a múltiplas CPUs, adaptando o escalonamento e a execução simultânea de tarefas. Adicionei controle individual de quantum e ociosidade, preempção e redução de migrações desnecessárias. Integrei as configurações à interface e realizei testes com RM, EDF e finalização automática, todos com resultados esperados.


Dia 5 - foi implementado a parte de modificação das características das tarefas/do simulador na interface, com mensagens de erro. Não testei muito a fundo, mas creio que a parte de "Integrar os controles da interface com o simulador" esteja funcionando (?)

**Dia 6 — Gráfico de Gantt:** Foi implementado o gráfico de Gantt utilizando o Canvas do Tkinter, integrado à interface do simulador. Adicionei o registro do histórico de execução das tarefas, identificação das CPUs, diferenciação visual dos estados (Pronta, Executando e Bloqueada), eventos de chegada, conclusão e perda de prazo, além de uma legenda e organização das tarefas por ID. Realizei testes com múltiplas CPUs, perda de prazo e bloqueio de tarefas, todos funcionando corretamente.
**Obs.:** Acredito que o gráfico também funcione em simulações mais longas, mas não tive tempo de testar. Seria interessante realizar esse teste para verificar se a visualização continua correta com muitos ticks e se será necessário adicionar rolagem horizontal.
