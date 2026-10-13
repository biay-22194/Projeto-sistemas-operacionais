

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
            
            for num_linha, linha in enumerate(linhas[1:], start=2):
                valores_tarefa = [v.strip().lower() for v in linha.split(';') if v.strip()]
                
                # Valida se a tarefa atual tem os 7 parâmetros
                if len(valores_tarefa) < 7:
                    return None, None, f"Erro na Linha {num_linha} (Tarefa): esperados 7 valores, encontrados {len(valores_tarefa)}."
                
                lista_tarefas_extraidas.append(valores_tarefa[:7])

            return config_so, lista_tarefas_extraidas, None

    except PermissionError:
        return None, None, "Erro: Sem permissão para abrir este arquivo."
    except Exception as e:
        return None, None, f"Erro ao ler arquivo: {str(e)}"