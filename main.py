"""
main.py — Orquestrador do pipeline Desafio Sefaz Maceio.

Este arquivo contem APENAS a orquestracao das etapas.
Toda logica de negocio esta nos modulos de src/.
"""

import logging
import time
import sys

import pandas as pd

from src.utils.constantes import (
    PASTA_COMPACTOS,
    PASTA_EXTRAIDOS,
    CAMINHO_PARQUET,
    CAMINHO_DUCKDB,
)
from src.utils.logger import configurar_logging
from src.pipeline.extrair_zips import extrair_zips
from src.pipeline.consolidar_dataframe import consolidar_todos_os_csvs
from src.pipeline.validar_dados import validar_dataframe
from src.pipeline.persistir_dados import salvar_em_parquet
from src.banco.conexao_duckdb import conectar
from src.banco.criar_tabela import criar_view_finbra
from src.analises.taxa_execucao import taxa_execucao
from src.analises.gasto_percapita import gasto_percapita
from src.analises.evolucao_temporal import evolucao_temporal
from src.analises.composicao_subfuncoes import composicao_subfuncoes
from src.visualizacao.graficos import gerar_graficos


def main() -> None:
    """Executa o pipeline completo do desafio."""
    configurar_logging()

    inicio = time.time()
    logging.info("Iniciando pipeline do Desafio Sefaz Maceio...")
    print()

    # --- 1-2. Extracao dos ZIPs ---
    logging.info("=" * 60)
    logging.info("ETAPA 1-2: EXTRACAO DOS ARQUIVOS ZIP")
    logging.info("=" * 60)
    extrair_zips(PASTA_COMPACTOS, PASTA_EXTRAIDOS)

    # --- 3-5. Consolidacao dos CSVs ---
    logging.info("=" * 60)
    logging.info("ETAPA 3-5: CONSOLIDACAO DOS CSVs")
    logging.info("=" * 60)
    df = consolidar_todos_os_csvs(PASTA_EXTRAIDOS)
    if df.empty:
        logging.error("DataFrame consolidado vazio. Verifique dados_extraidos/.")
        sys.exit(1)

    # --- 6. Validacao ---
    logging.info("=" * 60)
    logging.info("ETAPA 6: VALIDACAO DOS DADOS")
    logging.info("=" * 60)
    _exibir_relatorio_validacao(validar_dataframe(df))

    # --- 7. Persistencia em Parquet ---
    logging.info("=" * 60)
    logging.info("ETAPA 7: SALVANDO EM PARQUET")
    logging.info("=" * 60)
    salvar_em_parquet(df, CAMINHO_PARQUET)

    # --- 8. Banco DuckDB ---
    logging.info("=" * 60)
    logging.info("ETAPA 8: CRIANDO BANCO DUCKDB")
    logging.info("=" * 60)
    con = conectar(CAMINHO_DUCKDB)
    criar_view_finbra(con, CAMINHO_PARQUET)
    con.close()

    # --- 9. Analises SQL ---
    logging.info("=" * 60)
    logging.info("ETAPA 9: EXECUTANDO ANALISES SQL")
    logging.info("=" * 60)
    con = conectar(CAMINHO_DUCKDB)

    resultados = {
        "ranking": taxa_execucao(con),
        "percapita": gasto_percapita(con),
        "evolucao": evolucao_temporal(con),
        "subfuncoes": composicao_subfuncoes(con),
    }
    con.close()

    for nome, df_res in resultados.items():
        print(f"\n>>> {nome.upper()}")
        print(df_res.to_string(index=False))

    # --- 10. Graficos ---
    logging.info("=" * 60)
    logging.info("ETAPA 10: EXIBINDO GRAFICOS")
    logging.info("=" * 60)
    gerar_graficos(resultados)

    # --- Resumo ---
    fim = time.time()
    print()
    logging.info("=" * 60)
    logging.info(f"Pipeline finalizado com sucesso em {fim - inicio:.2f} segundos.")
    logging.info("=" * 60)


def _exibir_relatorio_validacao(resultados: dict) -> None:
    """Exibe o relatorio de validacao no terminal."""
    print("\n" + "=" * 50)
    print("       RELATORIO DE VALIDACAO DE DADOS")
    print("=" * 50)
    print(f"Tipo da coluna Valor: {resultados.get('tipo_valor')} "
          f"(Numerico: {resultados.get('valor_is_numeric')})")

    print("\nCapitais unicas por Ano:")
    for ano, qtd in sorted(resultados.get("capitais_por_ano", {}).items()):
        marcador = " [!] INCOMPLETO" if qtd < 26 else ""
        print(f"  {ano}: {qtd} capitais{marcador}")

    print("\nColunas com valores nulos:")
    tem_nulo = False
    for col, qtd in resultados.get("nulos", {}).items():
        if qtd > 0:
            print(f"  {col}: {qtd} nulos")
            tem_nulo = True
    if not tem_nulo:
        print("  Nenhum nulo encontrado!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
