import logging

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from src.visualizacao.utils_graficos import extrair_nome_capital


def gerar_graficos(resultados: dict[str, pd.DataFrame]) -> None:
    """Exibe os 4 gráficos na tela (sem salvar arquivo)."""
    plt.style.use("seaborn-v0_8-darkgrid")

    _grafico_ranking_execucao(resultados["ranking"])
    _grafico_per_capita(resultados["percapita"])
    _grafico_evolucao_maceio(resultados["evolucao"])
    _grafico_subfuncoes(resultados["subfuncoes"])


def _grafico_ranking_execucao(df: pd.DataFrame) -> None:
    """Top 10 Capitais — Taxa de Execução em Educação."""
    df_plot = df.head(10).copy()
    df_plot["Capital"] = df_plot["Instituição"].apply(extrair_nome_capital)

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
    plt.show()


def _grafico_per_capita(df: pd.DataFrame) -> None:
    """Top 10 Capitais — Gasto Per Capita em Educação (2024)."""
    df_plot = df.head(10).copy()
    df_plot["Capital"] = df_plot["Instituição"].apply(extrair_nome_capital)

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
    plt.show()


def _grafico_evolucao_maceio(df: pd.DataFrame) -> None:
    """Evolução Temporal — Maceió vs Média das Capitais."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df["Ano"], df["Taxa_Maceio"], marker="o", linewidth=2.5,
            label="Maceió", color="#1f77b4", markersize=8)
    ax.plot(df["Ano"], df["Taxa_Media_Outras"], marker="s", linewidth=2.5,
            label="Média das Outras Capitais", color="#ff7f0e", markersize=8, linestyle="--")

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
    plt.show()


def _grafico_subfuncoes(df: pd.DataFrame) -> None:
    """Composição de Subfunções da Educação (2024)."""
    df_plot = df.copy()
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
    plt.show()
