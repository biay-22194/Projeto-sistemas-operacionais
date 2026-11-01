

# ----------------------------------------------------------------------------------------------------------------------------------------------
# LÓGICA DE VALIDAÇÃO E LEITURA
def validar_configuracao(caminho_selecionado):
    try:
        with open(caminho_selecionado, 'r', encoding='utf-8') as ficheiro:
            # Filtra linhas vazias e remove quebras de linha
            linhas = [linha.strip() for linha in ficheiro if linha.strip()]

            # Garante que existe pelo menos a configuração do SO e 1 tarefa
            if len(linhas) < 2:
                return None, None, "Erro: O arquivo deve conter pelo menos 2 linhas (configuração do SO e uma tarefa)."

            # Processa configuração do SO
            linha1_valores = [v.strip().lower() for v in linhas[0].split(';') if v.strip()]
            
            if len(linha1_valores) < 3:
                return None, None, f"Erro na Linha 1: esperados 3 parâmetros do SO, encontrados {len(linha1_valores)}."
            
            config_so = linha1_valores[:3]

            # Processa tarefas
            lista_tarefas_extraidas = []
            ids_encontrados = set()
            
            for num_linha, linha in enumerate(linhas[1:], start=2):
                valores_tarefa = [v.strip().lower() for v in linha.split(';') if v.strip()]
                
                # Valida se a tarefa atual tem os 7 parâmetros
               
                # Verifica a quantidade de campos
                if len(valores_tarefa) != 7:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: a tarefa deve possuir exatamente 7 campos."
                    )

                # Verifica se a duração é um inteiro positivo
                try:
                    duracao = int(valores_tarefa[3])
                except ValueError:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: a duração deve ser um número inteiro."
                    )

                if duracao <= 0:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: a duração da tarefa "
                        f"'{valores_tarefa[0]}' deve ser maior que zero."
                    )

                # Verifica se o ID da tarefa já foi utilizado
                id_tarefa = valores_tarefa[0]
                
                if id_tarefa in ids_encontrados:
                    return (
                        None,
                        None,
                        f"Erro na linha {num_linha}: "
                        f"o ID '{id_tarefa}' está duplicado."
                    )
                
                ids_encontrados.add(id_tarefa)
                
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