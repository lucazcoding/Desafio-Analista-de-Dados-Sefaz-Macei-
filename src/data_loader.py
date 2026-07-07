import zipfile
from pathlib import Path
import pandas as pd
import duckdb
from src.data_transformer import descobrir_ano, limpar_e_transformar_df


def extrair_zips(pasta_compactos: Path, pasta_extraidos: Path) -> None:
    """Extrai todos os ZIPs encontrados em pasta_compactos para pasta_extraidos.

    Mantém a estrutura de diretórios original.

    Args:
        pasta_compactos: Caminho para a pasta contendo os arquivos ZIP.
        pasta_extraidos: Caminho para a pasta destino da extração.
    """
    pasta_extraidos.mkdir(parents=True, exist_ok=True)
    zips_encontrados = sorted(list(pasta_compactos.rglob("*.zip")))

    for caminho_zip in zips_encontrados:
        subpasta = caminho_zip.relative_to(pasta_compactos).parent
        destino = pasta_extraidos / subpasta
        destino.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(caminho_zip, "r") as zf:
            zf.extractall(destino)


def carregar_e_consolidar_csvs(pasta_extraidos: Path) -> pd.DataFrame:
    """Busca, lê, limpa e consolida todos os CSVs em pasta_extraidos.

    Args:
        pasta_extraidos: Caminho para a pasta onde os CSVs foram extraídos.

    Returns:
        DataFrame com todos os dados consolidados.
    """
    arquivos_csv = sorted(pasta_extraidos.rglob("*.csv"))
    dataframes = []

    for caminho_csv in arquivos_csv:
        ano = descobrir_ano(caminho_csv)
        df = pd.read_csv(
            caminho_csv,
            sep=";",
            skiprows=3,
            encoding="latin-1",
            decimal=",",
        )
        df_limpo = limpar_e_transformar_df(df, ano)
        dataframes.append(df_limpo)

    return pd.concat(dataframes, ignore_index=True)


def salvar_parquet(df: pd.DataFrame, caminho_parquet: Path) -> None:
    """Salva o DataFrame consolidado no formato Parquet.

    Args:
        df: DataFrame consolidado.
        caminho_parquet: Caminho de destino para salvar o arquivo Parquet.
    """
    caminho_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho_parquet, engine="pyarrow", index=False)


def carregar_no_duckdb(
    caminho_parquet: Path,
    caminho_duckdb: Path,
    nome_tabela: str = "despesas_finbra",
) -> None:
    """Cria a tabela no DuckDB a partir do arquivo Parquet, caso ela não exista.

    Args:
        caminho_parquet: Caminho para o arquivo Parquet consolidado.
        caminho_duckdb: Caminho para o arquivo do banco DuckDB.
        nome_tabela: Nome da tabela a ser criada no DuckDB.
    """
    con = duckdb.connect(str(caminho_duckdb))
    try:
        existe = con.execute(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{nome_tabela}'"
        ).fetchone()[0]

        if existe:
            print(f"Tabela {nome_tabela} já existe. Pulando criação.")
        else:
            con.execute(
                f"CREATE TABLE {nome_tabela} AS SELECT * FROM read_parquet('{caminho_parquet}')"
            )
            print(f"Tabela {nome_tabela} criada.")
    finally:
        con.close()
