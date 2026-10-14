Dia 1: estrutura da TCB, pega arquivos txt com as configurações e os salva. OBS: não foi feita a visualização das tarefas na interface (melhor fazer depois).

Dia 2 — Motor da Simulação

Criei o arquivo simulator.py, responsável por controlar a execução das tarefas.

Implementei o relógio global, que avança em ticks.

Implementei a ativação periódica das tarefas, com limite de 10 ativações por tarefa.

Adicionei o controle dos estados, do tempo restante de execução e da verificação de prazos (deadlines).

Criei um escalonador provisório que seleciona a primeira tarefa disponível.

Integrei o simulador à interface gráfica, adicionando o botão Avançar Tick e o contador de tempo.

Status: a implementação está pronta e a interface abre normalmente, mas ainda falta testar a execução com um arquivo de configuração.