import typer

from src.cli.commands import build_pipeline, run_analysis, run_all, list_analyses

app = typer.Typer(
    help="Sistema de analise SEFAZ Maceio - Desafio Analista de Dados",
    no_args_is_help=True,
)


@app.command()
def build() -> None:
    """Executa o pipeline ETL completo (extrair, consolidar, validar, parquet, duckdb)."""
    build_pipeline()


@app.command()
def analyze(
    nome: str = typer.Argument(
        help="Nome da analise: taxa, percapita, evolucao, subfuncoes"
    ),
) -> None:
    """Executa uma analise especifica e exibe o resultado."""
    run_analysis(nome)


@app.command()
def analyses() -> None:
    """Lista todas as analises disponiveis."""
    list_analyses()


@app.command()
def run() -> None:
    """Executa todas as analises e exibe os resultados."""
    run_all()
