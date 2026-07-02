"""
main.py — Pipeline completo do Desafio Sefaz Maceió.

Orquestra todo o fluxo de dados:
  1-2.  Extração dos ZIPs
  3-5.  Consolidação dos CSVs (carregar + descobrir ano + enriquecer)
  6.    Validação dos dados consolidados
  7.    Persistência em Parquet
  8.    Criação/atualização do banco DuckDB
  9.    Execução das 4 análises SQL
  10.   Geração de gráficos

Uso:
    python main.py
"""

import logging
import time
import sys

import pandas as pd
# pyrefly: ignore [missing-import]
import matplotlib
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------------------------------------------------------------------
# Imports dos helpers do projeto
# ---------------------------------------------------------------------------
from helpers.extrair_zips import extrair_zips
from helpers.consolidar_dataframe import consolidar_todos_os_csvs
from helpers.validar_dados import validar_dataframe
from helpers.persistir_dados import salvar_em_parquet, criar_banco_duckdb
from helpers.analises import (
    analise_ranking_execucao,
    analise_per_capita,
    analise_evolucao_maceio,
    analise_composicao_subfuncoes,
)
from helpers.gerar_tabelas import gerar_tabelas

# ---------------------------------------------------------------------------
# Constantes — caminhos relativos à raiz do projeto
# ---------------------------------------------------------------------------
DIRETORIO_BASE = Path(__file__).parent
PASTA_COMPACTOS = DIRETORIO_BASE / "dados_compactos"
PASTA_EXTRAIDOS = DIRETORIO_BASE / "dados_extraidos"
CAMINHO_PARQUET = PASTA_EXTRAIDOS / "finbra_consolidado.parquet"
CAMINHO_DUCKDB = DIRETORIO_BASE / "finbra.duckdb"
PASTA_GRAFICOS = DIRETORIO_BASE / "graficos"
PASTA_TABELAS = DIRETORIO_BASE / "tabelas"


# ===========================================================================
# Configuração
# ===========================================================================

def configurar_ambiente() -> None:
    """Configura logging, exibição do pandas e cria pastas de saída."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    # Evita notação científica nos valores monetários
    pd.options.display.float_format = "{:,.2f}".format

    # Garante encoding UTF-8 no terminal Windows (cp1252 não suporta acentos/emojis)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Backend não-interativo para salvar PNGs sem abrir janela
    matplotlib.use("Agg")

    # Garante que a pasta de gráficos exista
    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)


# ===========================================================================
# Etapas do pipeline
# ===========================================================================

def etapa_extracao() -> None:
    """Etapas 1-2: Localiza os .zip e extrai para dados_extraidos/."""
    logging.info("=" * 60)
    logging.info("ETAPA 1-2: EXTRAÇÃO DOS ARQUIVOS ZIP")
    logging.info("=" * 60)
    extrair_zips(PASTA_COMPACTOS, PASTA_EXTRAIDOS)


def etapa_consolidacao() -> pd.DataFrame:
    """Etapas 3-5: Lê cada CSV, descobre ano, enriquece e consolida tudo."""
    logging.info("=" * 60)
    logging.info("ETAPA 3-5: CONSOLIDAÇÃO DOS CSVs")
    logging.info("=" * 60)
    df = consolidar_todos_os_csvs(PASTA_EXTRAIDOS)
    if df.empty:
        logging.error("O DataFrame consolidado está vazio. Verifique os dados em dados_extraidos/.")
        sys.exit(1)
    return df


def etapa_validacao(df: pd.DataFrame) -> None:
    """Etapa 6: Executa testes de sanidade e imprime relatório."""
    logging.info("=" * 60)
    logging.info("ETAPA 6: VALIDAÇÃO DOS DADOS")
    logging.info("=" * 60)

    resultados = validar_dataframe(df)

    print("\n" + "=" * 50)
    print("       RELATÓRIO DE VALIDAÇÃO DE DADOS")
    print("=" * 50)
    print(f"Tipo da coluna Valor: {resultados.get('tipo_valor')} "
          f"(Numérico: {resultados.get('valor_is_numeric')})")

    print("\nCapitais únicas por Ano:")
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


def etapa_persistencia(df: pd.DataFrame) -> None:
    """Etapas 7-8: Salva Parquet e cria/atualiza DuckDB."""
    logging.info("=" * 60)
    logging.info("ETAPA 7: SALVANDO EM PARQUET")
    logging.info("=" * 60)
    salvar_em_parquet(df, CAMINHO_PARQUET)

    logging.info("=" * 60)
    logging.info("ETAPA 8: CRIANDO/ATUALIZANDO BANCO DUCKDB")
    logging.info("=" * 60)
    # Cria a view e já fecha — as análises vão reconectar
    con = criar_banco_duckdb(CAMINHO_PARQUET, CAMINHO_DUCKDB)
    con.close()


def etapa_analises() -> dict[str, pd.DataFrame]:
    """Etapa 9: Executa as 4 análises SQL via DuckDB e retorna os DataFrames."""
    logging.info("=" * 60)
    logging.info("ETAPA 9: EXECUTANDO ANÁLISES SQL")
    logging.info("=" * 60)

    # pyrefly: ignore [missing-import]
    import duckdb
    con = duckdb.connect(str(CAMINHO_DUCKDB))

    # 1 — Ranking de Execução em Educação
    logging.info("\n>>> Análise 1: Ranking de Execução em Educação (2020-2024)")
    df_ranking = analise_ranking_execucao(con)
    print("\n" + df_ranking.to_string(index=False))

    # 2 — Gasto Per Capita em Educação
    logging.info("\n>>> Análise 2: Gasto Per Capita em Educação (2024)")
    df_percapita = analise_per_capita(con)
    print("\n" + df_percapita.to_string(index=False))

    # 3 — Evolução Temporal Maceió vs Média
    logging.info("\n>>> Análise 3: Evolução Maceió vs Média das Capitais")
    df_evolucao = analise_evolucao_maceio(con)
    print("\n" + df_evolucao.to_string(index=False))

    # 4 — Composição de Subfunções da Educação
    logging.info("\n>>> Análise 4: Composição de Subfunções da Educação (2024)")
    df_subfuncoes = analise_composicao_subfuncoes(con)
    print("\n" + df_subfuncoes.to_string(index=False))

    con.close()

    return {
        "ranking": df_ranking,
        "percapita": df_percapita,
        "evolucao": df_evolucao,
        "subfuncoes": df_subfuncoes,
    }


def etapa_graficos(resultados: dict[str, pd.DataFrame]) -> None:
    """Etapa 10: Gera 4 gráficos PNG a partir dos DataFrames das análises."""
    logging.info("=" * 60)
    logging.info("ETAPA 10: GERANDO GRÁFICOS")
    logging.info("=" * 60)

    plt.style.use("seaborn-v0_8-darkgrid")

    _grafico_ranking_execucao(resultados["ranking"])
    _grafico_per_capita(resultados["percapita"])
    _grafico_evolucao_maceio(resultados["evolucao"])
    _grafico_subfuncoes(resultados["subfuncoes"])

    logging.info(f"Todos os gráficos salvos em '{PASTA_GRAFICOS}'.")


def etapa_tabelas(resultados: dict[str, pd.DataFrame]) -> None:
    """Gera tabelas HTML estilizadas para cada análise."""
    logging.info("=" * 60)
    logging.info("ETAPA EXTRA: GERANDO TABELAS HTML")
    logging.info("=" * 60)
    gerar_tabelas(resultados, PASTA_TABELAS)
    logging.info(f"Tabelas HTML salvas em '{PASTA_TABELAS}/'.")


# ===========================================================================
# Funções de geração de gráficos (privadas)
# ===========================================================================

def _extrair_nome_capital(texto: str) -> str:
    """
    Extrai o nome limpo da capital a partir do texto da Instituição.
    Ex: 'Prefeitura Municipal de Maceió - AL' → 'Maceió'
    """
    nome = texto.replace("Prefeitura Municipal de ", "").replace("Prefeitura Municipal do ", "")
    nome = nome.split(" - ")[0].strip()
    return nome


def _grafico_ranking_execucao(df: pd.DataFrame) -> None:
    """Gráfico 1: Top 10 Capitais — Taxa de Execução em Educação."""
    df_plot = df.head(10).copy()
    df_plot["Capital"] = df_plot["Instituição"].apply(_extrair_nome_capital)

    fig, ax = plt.subplots(figsize=(12, 7))

    cores = plt.cm.RdYlGn(df_plot["Taxa_Execucao"].values / 100)
    barras = ax.barh(df_plot["Capital"], df_plot["Taxa_Execucao"], color=cores, edgecolor="white")

    for barra, valor in zip(barras, df_plot["Taxa_Execucao"]):
        ax.text(barra.get_width() + 0.3, barra.get_y() + barra.get_height() / 2,
                f"{valor:.1f}%", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Taxa de Execução (%)", fontsize=12)
    ax.set_title("Top 10 Capitais — Taxa de Execução em Educação (2020-2024)", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(PASTA_GRAFICOS / "ranking_execucao.png", dpi=150)
    plt.close(fig)
    logging.info("  ✓ ranking_execucao.png salvo.")


def _grafico_per_capita(df: pd.DataFrame) -> None:
    """Gráfico 2: Top 10 Capitais — Gasto Per Capita em Educação (2024)."""
    df_plot = df.head(10).copy()
    df_plot["Capital"] = df_plot["Instituição"].apply(_extrair_nome_capital)

    fig, ax = plt.subplots(figsize=(12, 7))

    cores = plt.cm.YlGnBu([0.3 + 0.07 * i for i in range(len(df_plot))])
    barras = ax.barh(df_plot["Capital"], df_plot["Per_Capita"], color=cores, edgecolor="white")

    for barra, valor in zip(barras, df_plot["Per_Capita"]):
        ax.text(barra.get_width() + 10, barra.get_y() + barra.get_height() / 2,
                f"R$ {valor:,.2f}", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Gasto Per Capita (R$)", fontsize=12)
    ax.set_title("Top 10 Capitais — Gasto Per Capita em Educação (2024)", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(PASTA_GRAFICOS / "per_capita.png", dpi=150)
    plt.close(fig)
    logging.info("  ✓ per_capita.png salvo.")


def _grafico_evolucao_maceio(df: pd.DataFrame) -> None:
    """Gráfico 3: Evolução Temporal — Maceió vs Média das Capitais."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df["Ano"], df["Taxa_Maceio"], marker="o", linewidth=2.5,
            label="Maceió", color="#1f77b4", markersize=8)
    ax.plot(df["Ano"], df["Taxa_Media_Outras"], marker="s", linewidth=2.5,
            label="Média das Outras Capitais", color="#ff7f0e", markersize=8, linestyle="--")

    # Anota os valores sobre cada ponto
    for _, row in df.iterrows():
        ax.annotate(f"{row['Taxa_Maceio']:.1f}%",
                    (row["Ano"], row["Taxa_Maceio"]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=9, fontweight="bold", color="#1f77b4")
        ax.annotate(f"{row['Taxa_Media_Outras']:.1f}%",
                    (row["Ano"], row["Taxa_Media_Outras"]),
                    textcoords="offset points", xytext=(0, -15),
                    ha="center", fontsize=9, fontweight="bold", color="#ff7f0e")

    ax.set_xlabel("Ano", fontsize=12)
    ax.set_ylabel("Taxa de Execução (%)", fontsize=12)
    ax.set_title("Evolução da Taxa de Execução em Educação\nMaceió vs Média das Capitais (2020-2024)",
                 fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.set_xticks(df["Ano"])
    plt.tight_layout()
    fig.savefig(PASTA_GRAFICOS / "evolucao_maceio.png", dpi=150)
    plt.close(fig)
    logging.info("  ✓ evolucao_maceio.png salvo.")


def _grafico_subfuncoes(df: pd.DataFrame) -> None:
    """Gráfico 4: Composição de Subfunções da Educação (2024)."""
    df_plot = df.copy()
    # Limpa o nome da conta para exibição
    df_plot["Conta_Limpa"] = df_plot["Conta"].str.strip()

    fig, ax = plt.subplots(figsize=(12, 7))

    cores = plt.cm.Set2([i / len(df_plot) for i in range(len(df_plot))])
    barras = ax.barh(df_plot["Conta_Limpa"], df_plot["Percentual_do_Total"], color=cores, edgecolor="white")

    for barra, valor in zip(barras, df_plot["Percentual_do_Total"]):
        ax.text(barra.get_width() + 0.3, barra.get_y() + barra.get_height() / 2,
                f"{valor:.1f}%", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("Participação no Total (%)", fontsize=12)
    ax.set_title("Composição das Subfunções da Educação — Todas as Capitais (2024)",
                 fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(PASTA_GRAFICOS / "subfuncoes.png", dpi=150)
    plt.close(fig)
    logging.info("  ✓ subfuncoes.png salvo.")


# ===========================================================================
# Ponto de entrada
# ===========================================================================

def main() -> None:
    """Executa o pipeline completo do desafio."""
    configurar_ambiente()

    inicio_total = time.time()
    logging.info("🚀 Iniciando pipeline do Desafio Sefaz Maceió...")
    print()

    # Etapas 1-2: Extração
    etapa_extracao()

    # Etapas 3-5: Consolidação
    df_consolidado = etapa_consolidacao()

    # Etapa 6: Validação
    etapa_validacao(df_consolidado)

    # Etapas 7-8: Persistência
    etapa_persistencia(df_consolidado)

    # Etapa 9: Análises SQL
    resultados = etapa_analises()

    # Etapa 10: Gráficos
    etapa_graficos(resultados)

    # Tabelas HTML
    etapa_tabelas(resultados)

    # Tempo total
    fim_total = time.time()
    duracao = fim_total - inicio_total

    print()
    logging.info("=" * 60)
    logging.info(f"✅ Pipeline finalizado com sucesso em {duracao:.2f} segundos.")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
