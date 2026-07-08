"""
Testes de sanidade para as funções de transformação do pipeline FINBRA.

Testa as funções criadas na Etapa 2 (modularização), SEM inventar
regras de negócio novas além das que já existem no pipeline original.
"""

import re
from pathlib import Path

# pyrefly: ignore [missing-import]
import duckdb
import pandas as pd
import pytest

from src.data_transformer import classificar_conta, descobrir_ano, limpar_e_transformar_df
from src.utils.constantes import CAMINHO_DUCKDB, CAMINHO_PARQUET


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def df_raw():
    """DataFrame consolidado lido diretamente do Parquet (sem filtragem)."""
    return pd.read_parquet(CAMINHO_PARQUET)


@pytest.fixture(scope="session")
def df_funcoes(df_raw):
    """Somente linhas de ContaTipo == 'Função' e Ano entre 2020 e 2024."""
    return df_raw[
        (df_raw["ContaTipo"] == "Função")
        & (df_raw["Ano"].between(2020, 2024))
    ].copy()


@pytest.fixture(scope="session")
def df_subfuncoes(df_raw):
    """Somente linhas de ContaTipo == 'Subfunção'."""
    return df_raw[df_raw["ContaTipo"] == "Subfunção"].copy()


@pytest.fixture(scope="session")
def con():
    """Conexão ao DuckDB — aberta uma vez por sessão de testes."""
    c = duckdb.connect(str(CAMINHO_DUCKDB))
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Teste 1: coluna Valor é numérica após transformação
# ---------------------------------------------------------------------------

def test_valor_e_numerico(df_raw):
    """Após a conversão de decimal, a coluna 'Valor' deve ser do tipo numérico."""
    assert pd.api.types.is_numeric_dtype(df_raw["Valor"]), (
        f"Esperado tipo numérico, obtido: {df_raw['Valor'].dtype}"
    )


# ---------------------------------------------------------------------------
# Teste 2: sem linhas duplicadas para a combinação chave
# ---------------------------------------------------------------------------

def test_sem_duplicatas_chave(df_raw):
    """Não devem existir linhas duplicadas para a combinação
    (Instituição, Conta, Coluna, Ano).
    """
    chave = ["Instituição", "Conta", "Coluna", "Ano"]
    duplicatas = df_raw.duplicated(subset=chave).sum()
    assert duplicatas == 0, (
        f"Encontradas {duplicatas} linhas duplicadas na combinação {chave}."
    )


# ---------------------------------------------------------------------------
# Teste 3: soma das subfunções bate com o total da função (tolerância 0.01)
# ---------------------------------------------------------------------------

def test_soma_subfuncoes_igual_funcao(con):
    """A soma dos valores das subfunções (incluindo as agregadas) de uma
    função deve bater com o total declarado para essa função (tolerância
    de 0.01 para arredondamento).

    Verifica apenas 'Despesas Pagas' e 'Despesas Empenhadas' para cada par
    (Instituição, FuncaoBase, Coluna, Ano).

    Nota: além de ContaTipo = 'Subfunção' (ex.: "10.301 - Atenção Básica"),
    também é somado ContaTipo = 'Subfuncao_agregada' (ex.: "FU26 - Demais
    Subfunções"), que representa parte do detalhamento que o ente
    federativo optou por não especificar por subfunção individual. Sem
    incluir essa categoria, o teste acusava divergências de milhões de
    reais que na verdade eram dado legítimo, não erro do pipeline.
    """
    resultado = con.execute("""
        WITH funcoes AS (
            SELECT
                Instituição,
                Ano,
                Coluna,
                -- Extrai o prefixo "DD" da conta de função (ex: "10" de "10 - Saúde")
                regexp_extract(Conta, '^(\\d{2})\\s*-', 1) AS FuncaoBase,
                Valor AS TotalFuncao
            FROM despesas_finbra
            WHERE ContaTipo = 'Função'
              AND Ano BETWEEN 2020 AND 2024
              AND Coluna IN ('Despesas Pagas', 'Despesas Empenhadas')
        ),
        subfuncoes AS (
            SELECT
                Instituição,
                Ano,
                Coluna,
                -- Extrai o prefixo "DD": de "10.301 - Atenção Básica" (Subfunção)
                -- ou de "FU26 - Demais Subfunções" (Subfuncao_agregada)
                COALESCE(
                    NULLIF(regexp_extract(Conta, '^(\\d{2})\\.\\d{3}\\s*-', 1), ''),
                    NULLIF(regexp_extract(Conta, '^FU(\\d{2})', 1), '')
                ) AS FuncaoBase,
                SUM(Valor) AS SomaSub
            FROM despesas_finbra
            WHERE ContaTipo IN ('Subfunção', 'Subfuncao_agregada')
              AND Ano BETWEEN 2020 AND 2024
              AND Coluna IN ('Despesas Pagas', 'Despesas Empenhadas')
            GROUP BY Instituição, Ano, Coluna, FuncaoBase
        )
        SELECT
            f.Instituição,
            f.Ano,
            f.Coluna,
            f.FuncaoBase,
            f.TotalFuncao,
            s.SomaSub,
            ABS(f.TotalFuncao - s.SomaSub) AS Diferenca
        FROM funcoes f
        JOIN subfuncoes s
            ON f.Instituição = s.Instituição
           AND f.Ano         = s.Ano
           AND f.Coluna      = s.Coluna
           AND f.FuncaoBase  = s.FuncaoBase
        WHERE ABS(f.TotalFuncao - s.SomaSub) > 0.01
    """).df()

    assert len(resultado) == 0, (
        f"Encontradas {len(resultado)} combinações onde a soma das subfunções "
        f"(incluindo agregadas) diverge do total da função em mais de 0.01:\n"
        f"{resultado.head(10).to_string()}"
    )


# ---------------------------------------------------------------------------
# Teste 4: todos os anos no dataset estão entre 2020 e 2025
# ---------------------------------------------------------------------------

def test_anos_no_intervalo_valido(df_raw):
    """Todos os anos presentes no dataset devem estar entre 2020 e 2025
    (inclusive), conforme escopo do desafio.
    """
    anos_fora = df_raw[~df_raw["Ano"].between(2020, 2025)]["Ano"].unique()
    assert len(anos_fora) == 0, (
        f"Anos fora do intervalo [2020, 2025] encontrados: {sorted(anos_fora)}"
    )


# ---------------------------------------------------------------------------
# Testes auxiliares: cobertura das funções de data_transformer
# ---------------------------------------------------------------------------

class TestClassificarConta:
    """Testes unitários de classificar_conta — baseados nos casos originais
    do notebook 1-Preparar_Dataset.ipynb."""

    def test_total_geral_despesas_exceto(self):
        assert classificar_conta("Despesas Exceto Intraorçamentárias") == "Total_Geral"

    def test_total_geral_despesas_intra(self):
        assert classificar_conta("Despesas Intraorçamentárias") == "Total_Geral"

    def test_funcao(self):
        assert classificar_conta("10 - Saúde") == "Função"

    def test_subfuncao(self):
        assert classificar_conta("10.301 - Atenção Básica") == "Subfunção"

    def test_subfuncao_agregada(self):
        assert classificar_conta("FU10 - Demais Subfunções") == "Subfuncao_agregada"

    def test_nao_string_retorna_outros(self):
        assert classificar_conta(None) == "Outros"
        assert classificar_conta(42) == "Outros"


class TestDescobrirAno:
    """Testes unitários de descobrir_ano."""

    def test_ano_detectado_na_pasta(self, tmp_path):
        p = tmp_path / "2022" / "finbra.csv"
        p.parent.mkdir(parents=True)
        assert descobrir_ano(p) == 2022

    def test_ano_nao_encontrado_levanta_erro(self, tmp_path):
        p = tmp_path / "dados" / "finbra.csv"
        p.parent.mkdir(parents=True)
        with pytest.raises(ValueError, match="Ano não encontrado"):
            descobrir_ano(p)


class TestLimparTransformarDf:
    """Testes unitários de limpar_e_transformar_df."""

    def test_valor_e_numerico_apos_transformacao(self):
        df = pd.DataFrame({
            "Conta": ["10 - Saúde", "10.301 - Atenção Básica"],
            "Valor": ["1.234,56", "789,00"],
            "Coluna": ["Despesas Pagas", "Despesas Pagas"],
        })
        # Simula o que o read_csv com decimal=',' já fez — Valor já é float
        df["Valor"] = [1234.56, 789.00]
        resultado = limpar_e_transformar_df(df, ano=2022)
        assert pd.api.types.is_numeric_dtype(resultado["Valor"])

    def test_coluna_ano_preenchida(self):
        df = pd.DataFrame({"Conta": ["10 - Saúde"], "Valor": [100.0], "Coluna": ["Despesas Pagas"]})
        resultado = limpar_e_transformar_df(df, ano=2023)
        assert (resultado["Ano"] == 2023).all()

    def test_conta_tipo_classificado(self):
        df = pd.DataFrame({
            "Conta": ["10 - Saúde", "10.301 - Atenção Básica"],
            "Valor": [1000.0, 500.0],
            "Coluna": ["Despesas Pagas", "Despesas Pagas"],
        })
        resultado = limpar_e_transformar_df(df, ano=2022)
        assert resultado.loc[resultado["Conta"] == "10 - Saúde", "ContaTipo"].iloc[0] == "Função"
        assert resultado.loc[resultado["Conta"] == "10.301 - Atenção Básica", "ContaTipo"].iloc[0] == "Subfunção"
