# Simulador Visual de Escalonamento de Tarefas — Projeto A

Projeto acadêmico de **Sistemas Operacionais**, desenvolvido em **Python**, para simular o escalonamento de tarefas periódicas em uma ou mais CPUs. A aplicação permite acompanhar a execução por ticks, comparar os algoritmos **Rate Monotonic (RM)** e **Earliest Deadline First (EDF)** e visualizar o resultado em um **gráfico de Gantt**.

## Funcionalidades

- Importação de arquivos de configuração `.txt` com parâmetros do sistema e das tarefas.
- Representação das tarefas por estruturas do tipo **TCB (Task Control Block)**.
- Escalonamento por **RM** (prioridade associada ao período) e **EDF** (prioridade associada ao prazo absoluto mais próximo).
- Simulação por ticks, com chegada e ativação periódica de tarefas, limitada a **10 ativações por tarefa periódica**.
- Execução em **múltiplas CPUs**, com preempção, controle de quantum e registro da ociosidade.
- Acompanhamento dos estados das tarefas: **Nova, Pronta, Executando, Bloqueada e Concluída** (tarefas aperiódicas podem ser exibidas como ignoradas).
- Identificação de eventos de **chegada, conclusão e perda de prazo**.
- Interface gráfica para alterar parâmetros do sistema e características das tarefas, com mensagens de validação.
- Execução passo a passo ou automática, com possibilidade de pausar e **retroceder ticks**.
- Armazenamento de estados anteriores (*snapshots*) e continuação após alterações.
- Gráfico de Gantt com cores, identificação de CPUs, estados e marcadores de eventos.
- **Exportação do gráfico completo para PNG**, inclusive em simulações longas.

## Tecnologias e dependências

- Python 3
- Tkinter (interface gráfica básica)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (componentes da interface)
- [CTkTable](https://github.com/Akascape/CTkTable) (tabelas)
- [Pillow](https://pillow.readthedocs.io/) (exportação para PNG)

O Tkinter costuma vir com instalações de Python para Windows; em algumas distribuições Linux, pode ser necessário instalar o pacote do sistema (`python3-tk`).

## Instalação e execução

Na pasta do projeto, crie e ative um ambiente virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Em Windows, a ativação é feita por `.venv\Scripts\activate` no Prompt de Comando.

Instale as bibliotecas externas:

```bash
python -m pip install customtkinter CTkTable Pillow
```

Execute a interface:

```bash
python main.py
```

> Os módulos `main.py`, `interface.py`, `simulator.py`, `structs.py`, `utils.py` e `gantt.py` devem estar na mesma pasta, com esses nomes. Os arquivos de teste são opcionais para iniciar o aplicativo.

## Formato do arquivo de configuração

O simulador lê um arquivo de texto com **campos separados por ponto e vírgula (`;`)**. A primeira linha configura o sistema; as linhas seguintes descrevem as tarefas.

**Primeira linha:**

```text
algoritmo;quantum;quantidade_cpus
```

- `algoritmo`: `rm` ou `edf`.
- `quantum`: inteiro maior que zero.
- `quantidade_cpus`: inteiro maior que zero.

**Demais linhas:**

```text
id;cor;ingresso;duracao;periodo;prazo;lista_eventos
```

- `id`: identificador único da tarefa.
- `cor`: nome de cor reconhecido pela interface (por exemplo, `red`, `blue`, `green`) ou código hexadecimal válido.
- `ingresso`: tick inicial de chegada (não negativo).
- `duracao`: quantidade de ticks de CPU exigidos por ativação (maior que zero).
- `periodo`: intervalo entre ativações; valores positivos indicam tarefas periódicas. Na implementação atual, `0` indica tarefa aperiódica, não escalonada pelo motor periódico.
- `prazo`: prazo relativo para concluir cada ativação (maior que zero).
- `lista_eventos`: campo presente no formato de entrada; nos testes fornecidos foi utilizado `[]`.

**Exemplo (`exemplo.txt`):**

```text
rm;2;2
A;red;0;2;5;5;[]
B;blue;0;3;10;10;[]
C;green;0;1;8;8;[]
```

O prazo absoluto de cada ativação é calculado a partir do instante dessa ativação mais o prazo relativo. O programa registra uma perda de prazo caso a ocorrência ainda não tenha sido concluída quando o prazo é atingido.

## Como utilizar

1. Execute `main.py`.
2. Clique em **Carregar Arquivo .TXT** e selecione uma configuração.
3. Confira o algoritmo, o quantum, o número de CPUs e as tarefas cadastradas.
4. Use **Avançar Tick** para simular uma unidade de tempo, ou **Execução Automática** para avançar continuamente; o botão permite pausar.
5. Acompanhe os estados na tabela e as execuções no gráfico de Gantt.
6. Use **Retroceder Tick** para consultar estados anteriores. É possível editar características de tarefas e prosseguir a partir do estado restaurado.
7. Clique em **Exportar Gantt (PNG)** para escolher o local de salvamento da imagem.

## Interpretação do gráfico de Gantt

- **Retângulos coloridos:** execução de uma tarefa; o número indica a CPU utilizada.
- **Contorno com `P`:** tarefa pronta.
- **Retângulo cinza com `X`:** tarefa bloqueada.
- **Triângulo verde:** chegada/ativação.
- **Marcador azul:** conclusão.
- **`X` vermelho:** perda de prazo.

As tarefas são organizadas por identificador no eixo vertical; o eixo horizontal representa os ticks da simulação.

## Testes realizados

Durante a revisão final, foram executados testes manuais de:

| Categoria | Casos verificados |
|---|---|
| Escalonamento | RM e EDF; chegada de tarefa mais prioritária; preempção |
| Multiprocessamento | Execução com duas CPUs e tarefas concorrentes |
| Prioridades | Empate em RM e preferência por tarefa já em execução |
| Prazos | Detecção de perda de deadline e continuidade da tarefa |
| Entradas inválidas | Algoritmo inválido, zero CPUs, quantum nulo/negativo, duração nula/negativa, período negativo, prazo zero, campos faltantes, valor não numérico e arquivo vazio |
| Identificadores | Teste com IDs diferentes; foi adicionada validação para IDs repetidos, cuja rejeição deve ser confirmada na revisão final |
| Histórico | Retrocesso, edição da cor e da duração, continuação e recálculo do histórico após edição |
| Exportação | Gantt em PNG e exportação de simulação longa, com verificação visual dos ticks, CPUs e marcadores |

Os testes confirmam os **cenários executados**, mas não substituem uma bateria automatizada de testes nem garantem ausência de defeitos em todos os casos possíveis.

## Estrutura do projeto

```text
Projeto-sistemas-operacionais/
├── main.py          # Ponto de entrada
├── interface.py     # Interface e controles do usuário
├── simulator.py     # Relógio, ocorrências, CPUs, histórico e eventos
├── structs.py       # TCB e algoritmos RM/EDF
├── utils.py         # Leitura e validação dos arquivos .txt
├── gantt.py         # Desenho e exportação do gráfico
├── teste_*.txt      # Configurações de teste (quando presentes)
└── README.md        # Documentação
```

## Empacotamento e entrega

O planejamento do projeto prevê criar um executável com **PyInstaller** e verificar sua execução sem instalações adicionais de bibliotecas Python na máquina de destino. **Essa etapa ainda precisa ser concluída e validada**; portanto, o procedimento de distribuição final não é apresentado aqui como já testado.

Para preparar o ambiente de empacotamento:

```bash
python -m pip install pyinstaller
```

O empacotamento deve ser realizado e testado no sistema operacional de destino: em geral, um executável gerado no Linux não é um `.exe` de Windows. Depois de gerar o artefato, é necessário verificar abertura da interface, carregamento dos `.txt`, simulação, retrocesso e exportação PNG em uma máquina ou ambiente limpo.

## Observações

- Tarefas com período `0` não são executadas pelo mecanismo periódico atual.
- Os resultados podem depender das características das tarefas, dos prazos e da quantidade de CPUs.
- O projeto foi desenvolvido para fins didáticos, como representação simplificada de conceitos de escalonamento de Sistemas Operacionais.
