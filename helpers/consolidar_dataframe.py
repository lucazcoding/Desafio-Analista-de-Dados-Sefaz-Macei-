import pandas as pd
from pathlib import Path
import logging

# Importando as funções dos nossos helpers já criados
from helpers.descobrir_ano import descobrir_ano_pelo_caminho
from helpers.carregar_csv import carregar_csv_finbra
from helpers.enriquecer_dataframe import enriquecer_dados_finbra

def consolidar_todos_os_csvs(pasta_dados_extraidos: str | Path) -> pd.DataFrame:
    """
    Percorre a pasta de dados extraídos, lê cada arquivo CSV, 
    descobre o ano pela pasta, enriquece os dados (Ano, ContaTipo)
    e une todos em um único DataFrame gigante.
    """
    pasta = Path(pasta_dados_extraidos)
    
    if not pasta.exists():
        logging.error(f"A pasta '{pasta}' não foi encontrada.")
        return pd.DataFrame()
        
    lista_dfs = []
    arquivos_csv = list(pasta.rglob("*.csv"))
    
    if not arquivos_csv:
        logging.warning("Nenhum arquivo .csv encontrado para consolidar.")
        return pd.DataFrame()
        
    logging.info(f"Iniciando processamento e consolidação de {len(arquivos_csv)} arquivo(s) CSV...")
    
    for caminho in arquivos_csv:
        try:
            # 1. Carrega os dados brutos do Siconfi (ignorando cabeçalho, acertando vírgula)
            df_bruto = carregar_csv_finbra(caminho)
            
            # 2. Descobre o ano pela pasta de origem (ex: 2022)
            ano = descobrir_ano_pelo_caminho(caminho)
            if ano is None:
                logging.warning(f"Ano não identificado para '{caminho}'. A coluna ficará vazia.")
                
            # 3. Enriquece adicionando colunas 'Ano', 'ContaTipo' e força 'Valor' para Numérico
            df_enriquecido = enriquecer_dados_finbra(df_bruto, ano)
            
            # 4. Guarda o DF pronto na lista
            lista_dfs.append(df_enriquecido)
            logging.info(f"[{ano}] '{caminho.name}' processado com sucesso. ({len(df_enriquecido)} linhas)")
            
        except Exception as e:
            logging.error(f"Erro crítico ao processar o arquivo '{caminho}': {e}")
            
    # Concatena todos os DataFrames da lista em um único grande DataFrame
    if lista_dfs:
        df_consolidado = pd.concat(lista_dfs, ignore_index=True)
        logging.info(f"Sucesso! Base consolidada gerada com {len(df_consolidado)} linhas.")
        return df_consolidado
        
    return pd.DataFrame()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Opção para o Pandas não exibir os valores como notação científica (o tal do e+08) e sim com duas casas decimais
    pd.options.display.float_format = '{:,.2f}'.format
    
    # Definindo a pasta base 
    diretorio_atual = Path(__file__).parent.parent
    pasta_extraidos = diretorio_atual / "dados_extraidos"
    
    # Chama a consolidação
    df_final = consolidar_todos_os_csvs(pasta_extraidos)
    
    if not df_final.empty:
        logging.info("\nAmostra dos dados (5 linhas aleatórias):")
        print(df_final[['Instituição', 'Ano', 'Conta', 'ContaTipo', 'Valor']].sample(5))
        
        logging.info("\nContagem de registros por ano:")
        print(df_final['Ano'].value_counts().sort_index())
