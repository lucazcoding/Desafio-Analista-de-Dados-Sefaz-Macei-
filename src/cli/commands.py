import sys
import logging

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
from src.visualizacao.graficos import (
    _grafico_ranking_execucao,
    _grafico_per_capita,
    _grafico_evolucao_maceio,
    _grafico_subfuncoes,
)

ANALISES_DISPONIVEIS = {
    "taxa": ("Taxa de Execucao em Educacao", "src.analises.taxa_execucao", "taxa_execucao"),
    "percapita": ("Gasto Per Capita em Educacao", "src.analises.gasto_percapita", "gasto_percapita"),
    "evolucao": ("Evolucao Temporal Maceio vs Media", "src.analises.evolucao_temporal", "evolucao_temporal"),
    "subfuncoes": ("Composicao de Subfuncoes da Educacao", "src.analises.composicao_subfuncoes", "composicao_subfuncoes"),
}

GRAFICOS_DISPONIVEIS = {
    "taxa": _grafico_ranking_execucao,
    "percapita": _grafico_per_capita,
    "evolucao": _grafico_evolucao_maceio,
    "subfuncoes": _grafico_subfuncoes,
}


def build_pipeline() -> None:
    """Executa o pipeline ETL completo."""
    configurar_logging()

    logging.info("Iniciando pipeline ETL...")

    extrair_zips(PASTA_COMPACTOS, PASTA_EXTRAIDOS)

    df = consolidar_todos_os_csvs(PASTA_EXTRAIDOS)
    if df.empty:
        logging.error("DataFrame consolidado vazio.")
        sys.exit(1)

    _exibir_relatorio_validacao(validar_dataframe(df))

    salvar_em_parquet(df, CAMINHO_PARQUET)

    con = conectar(CAMINHO_DUCKDB)
    criar_view_finbra(con, CAMINHO_PARQUET)
    con.close()

    print("\n✔ Pipeline ETL finalizado com sucesso.")


def run_analysis(nome: str) -> None:
    """Executa uma analise especifica pelo nome."""
    configurar_logging()

    if nome not in ANALISES_DISPONIVEIS:
        print(f"Analise '{nome}' nao encontrada.")
        print(f"Disponiveis: {', '.join(ANALISES_DISPONIVEIS.keys())}")
        sys.exit(1)

    descricao, modulo, funcao = ANALISES_DISPONIVEIS[nome]

    con = conectar(CAMINHO_DUCKDB)

    import importlib
    mod = importlib.import_module(modulo)
    func = getattr(mod, funcao)
    df = func(con)

    con.close()

    print(f"\n>>> {descricao.upper()}")
    print(df.to_string(index=False))

    grafico_func = GRAFICOS_DISPONIVEIS[nome]
    grafico_func(df)


def run_all() -> None:
    """Executa todas as analises e exibe os resultados."""
    configurar_logging()

    con = conectar(CAMINHO_DUCKDB)

    import importlib

    for nome, (descricao, modulo, funcao) in ANALISES_DISPONIVEIS.items():
        mod = importlib.import_module(modulo)
        func = getattr(mod, funcao)
        df = func(con)

        print(f"\n>>> {descricao.upper()}")
        print(df.to_string(index=False))

        grafico_func = GRAFICOS_DISPONIVEIS[nome]
        grafico_func(df)

    con.close()


def list_analyses() -> None:
    """Lista todas as analises disponiveis."""
    print("\nAnalises disponiveis:\n")
    for nome, (descricao, _, _) in ANALISES_DISPONIVEIS.items():
        print(f"  {nome:<12} - {descricao}")
    print()


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
