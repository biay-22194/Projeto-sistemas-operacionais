# ----------------------------------------------------------------------------------------------------------------------------------------------
# LÓGICA DE VALIDAÇÃO E LEITURA DE FICHEIROS DE CONFIGURAÇÃO
# ----------------------------------------------------------------------------------------------------------------------------------------------

def validar_configuracao(caminho_selecionado):
    """
    Lê e valida sintaticamente o ficheiro de texto de configuração da simulação.
    
    Estrutura esperada do ficheiro (delimitado por ';'):
    - Linha 1: algoritmo_escalonamento; quantum; qtde_cpus
    - Linhas 2+: id; cor; ingresso; duracao; periodo; prazo; lista_eventos
    
    Retorna uma tupla: (config_so, lista_tarefas_extraidas, mensagem_erro)
    - Se a validação for bem-sucedida: (list, list, None)
    - Se ocorrer um erro: (None, None, str_com_descricao_do_erro)
    """
    try:
        with open(caminho_selecionado, 'r', encoding='utf-8') as arquivo:
            # Remove espaços em branco nas extremidades e ignora linhas vazias
            linhas = [linha.strip() for linha in arquivo if linha.strip()]

            # Garante o requisito mínimo: 1 linha para o SO e pelo menos 1 linha de tarefa
            if len(linhas) < 2:
                return None, None, "Erro: O arquivo deve conter pelo menos 2 linhas (configuração do SO e uma tarefa)."

            # --- Processamento da Linha 1: Parâmetros do Sistema Operativo ---
            linha1_valores = [v.strip().lower() for v in linhas[0].split(';') if v.strip()]
            
            # Verifica se os 3 parâmetros globais essenciais foram fornecidos (Algoritmo, Quantum, CPUs)
            if len(linha1_valores) < 3:
                return None, None, f"Erro na Linha 1: esperados 3 parâmetros do SO, encontrados {len(linha1_valores)}."
            
            config_so = linha1_valores[:3]

            # --- Processamento das Linhas 2+: Mapeamento dos TCBs das Tarefas ---
            lista_tarefas_extraidas = []
            ids_encontrados = set()
            
            for num_linha, linha in enumerate(linhas[1:], start=2):
                # Normaliza e divide os atributos pelo delimitador ';'
                valores_tarefa = [v.strip().lower() for v in linha.split(';') if v.strip()]
                
                # Valida se a tarefa atual tem os 7 parâmetros
               
                
                lista_tarefas_extraidas.append(valores_tarefa)

                                # Validate period and deadline
                try:
                    periodo = int(valores_tarefa[4])
                    prazo = int(valores_tarefa[5])
                except ValueError:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: período e prazo devem ser números inteiros."
                    )

                if periodo < 0:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: o período não pode ser negativo."
                    )

                if prazo <= 0:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: o prazo deve ser maior que zero."
                    )
                    
        return config_so, lista_tarefas_extraidas, None

    except PermissionError:
        return None, None, "Erro: Sem permissão para abrir este arquivo."
    except Exception as e:
        return None, None, f"Erro ao ler arquivo: {str(e)}"