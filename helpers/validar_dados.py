import pandas as pd
import logging
from typing import Dict, Any

def validar_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executa testes de sanidade no DataFrame consolidado do Finbra.
    Retorna um dicionário com os resultados, útil para logs ou relatórios automatizados.
    
    Validações:
    1. Quantas capitais declararam dados por ano.
    2. Existência de valores nulos.
    3. Tipo de dado da coluna 'Valor' (deve ser numérico).
    """
    if df.empty:
        logging.warning("O DataFrame fornecido para validação está vazio.")
        return {"status": "vazio"}
        
    resultados = {}
    
    # 1. Contar capitais por ano (Instituição)
    capitais_por_ano = df.groupby('Ano')['Instituição'].nunique().to_dict()
    resultados['capitais_por_ano'] = capitais_por_ano
    
    # 2. Verificar nulos
    nulos_por_coluna = df.isnull().sum().to_dict()
    resultados['nulos'] = nulos_por_coluna
    
    # 3. Validar tipo numérico da coluna Valor
    is_numeric = pd.api.types.is_numeric_dtype(df['Valor'])
    resultados['valor_is_numeric'] = is_numeric
    resultados['tipo_valor'] = str(df['Valor'].dtype)
    
    # --- LOGS DE SANIDADE ---
    
    # Alerta sobre a completude de 2025
    qtd_2025 = capitais_por_ano.get(2025, 0)
    if qtd_2025 > 0 and qtd_2025 < 26:
        logging.warning(f"O ano de 2025 está INCOMPLETO! Apenas {qtd_2025} de 26 capitais enviaram os dados.")
        
    # Alerta sobre nulos no Valor
    qtd_nulos_valor = nulos_por_coluna.get('Valor', 0)
    if qtd_nulos_valor > 0:
        logging.warning(f"Existem {qtd_nulos_valor} valores nulos na coluna Valor. Cuidado ao somar!")
        
    # Alerta grave sobre tipo da coluna Valor
    if not is_numeric:
        logging.error("CRÍTICO: A coluna 'Valor' NÃO é numérica. Agregações e somas irão falhar!")
    else:
        logging.info("Validado: Coluna 'Valor' é numérica. OK!")
        
    return resultados

if __name__ == "__main__":
    # Teste local da validação
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    import sys
    from pathlib import Path
    
    # Garante que o python consiga achar o pacote helpers quando rodado como script
    diretorio_atual = Path(__file__).parent.parent
    sys.path.append(str(diretorio_atual))
    
    from helpers.consolidar_dataframe import consolidar_todos_os_csvs
    
    pasta_extraidos = diretorio_atual / "dados_extraidos"
    
    logging.info("Carregando toda a base consolidada para rodar a validação...")
    df_consolidado = consolidar_todos_os_csvs(pasta_extraidos)
    
    logging.info("Iniciando bateria de validações Sefaz...")
    resultados = validar_dataframe(df_consolidado)
    
    print("\n" + "="*40)
    print("RELATÓRIO DE VALIDAÇÃO DE DADOS")
    print("="*40)
    print(f"Tipo da coluna Valor: {resultados.get('tipo_valor')} (Numérico: {resultados.get('valor_is_numeric')})")
    print("\nCapitais únicas por Ano:")
    for ano, qtd in resultados.get('capitais_por_ano', {}).items():
        print(f"  {ano}: {qtd} capitais")
        
    print("\nColunas com valores nulos:")
    tem_nulo = False
    for col, qtd in resultados.get('nulos', {}).items():
        if qtd > 0:
            print(f"  {col}: {qtd} nulos")
            tem_nulo = True
            
    if not tem_nulo:
        print("  Nenhum nulo encontrado nas colunas!")
    print("="*40)
