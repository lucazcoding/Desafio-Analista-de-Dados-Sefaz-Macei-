import pandas as pd
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #f5f7fa;
    padding: 40px 20px;
    display: flex; flex-direction: column; align-items: center;
  }}
  .container {{
    max-width: 1200px; width: 100%;
    background: white; border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    padding: 32px; overflow-x: auto;
  }}
  h1 {{
    font-size: 22px; color: #1a1a2e; margin-bottom: 8px;
    font-weight: 700;
  }}
  .subtitulo {{
    font-size: 14px; color: #666; margin-bottom: 24px;
    border-bottom: 2px solid #e9ecef; padding-bottom: 12px;
  }}
  table {{
    width: 100%; border-collapse: collapse;
    font-size: 14px;
  }}
  thead th {{
    background: #1a1a2e; color: white; padding: 12px 14px;
    text-align: left; font-weight: 600;
    white-space: nowrap;
  }}
  thead th:first-child {{ border-radius: 8px 0 0 0; }}
  thead th:last-child {{ border-radius: 0 8px 0 0; }}
  tbody tr:nth-child(even) {{ background: #f8f9fa; }}
  tbody tr:hover {{ background: #e9ecef; }}
  tbody td {{
    padding: 10px 14px; border-bottom: 1px solid #e9ecef;
    white-space: nowrap;
  }}
  .num {{ text-align: right; font-family: 'JetBrains Mono', 'Consolas', monospace; }}
  .destaque {{ font-weight: 700; color: #e74c3c; }}
  .footer {{
    margin-top: 20px; text-align: center; font-size: 12px; color: #999;
  }}
  .tag {{
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: 12px; font-weight: 600;
  }}
  .tag-top {{ background: #d4edda; color: #155724; }}
  @media (max-width: 600px) {{
    .container {{ padding: 16px; }}
    table {{ font-size: 12px; }}
    thead th, tbody td {{ padding: 8px 6px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>{titulo}</h1>
  <div class="subtitulo">{descricao}</div>
  {tabela}
</div>
<div class="footer">Gerado por Desafio Sefaz Maceió — Análise de Dados FINBRA</div>
</body>
</html>"""


def _formatar_valor(valor) -> str:
    if pd.isna(valor):
        return "—"
    if isinstance(valor, float):
        if abs(valor) >= 1_000_000:
            return f"R$ {valor:,.2f}"
        elif abs(valor) >= 1_000:
            return f"R$ {valor:,.2f}"
        return f"{valor:,.2f}"
    return str(valor)


def _formatar_df(df: pd.DataFrame, colunas_moeda: list[str] | None = None) -> str:
    df = df.copy()
    if colunas_moeda is None:
        colunas_moeda = []
    cols_num = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    for col in cols_num:
        if col in colunas_moeda:
            df[col] = df[col].apply(_formatar_valor)
        elif col != "Ano":
            if any(df[col] > 1_000_000):
                df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
            elif df[col].dtype == "float64":
                if col in ("Taxa_Execucao", "Percentual_do_Total", "Taxa_Maceio", "Taxa_Media_Outras", "Per_Capita"):
                    df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
                else:
                    df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "—")
    html = df.to_html(index=False, escape=False, border=0)
    return html.replace('<table>', '<table class="tabela">')


def gerar_tabelas(resultados: dict[str, pd.DataFrame], pasta_destino: Path) -> None:
    pasta_destino.mkdir(parents=True, exist_ok=True)

    configs = [
        {
            "chave": "ranking",
            "titulo": "Ranking de Execução em Educação",
            "descricao": "Top 26 Capitais — Taxa de Execução (Pago ÷ Empenhado × 100) — Média 2020 a 2024",
            "moeda": ["Empenhado", "Pago"],
            "n": None,
        },
        {
            "chave": "percapita",
            "titulo": "Gasto Per Capita em Educação",
            "descricao": "Top 26 Capitais — Despesas Pagas por Habitante em Educação — Ano 2024",
            "moeda": ["Pago"],
            "n": None,
        },
        {
            "chave": "evolucao",
            "titulo": "Evolução Temporal — Maceió vs Média das Capitais",
            "descricao": "Taxa de Execução em Educação de 2020 a 2024 — Maceió comparado à média das demais capitais",
            "moeda": [],
            "n": None,
        },
        {
            "chave": "subfuncoes",
            "titulo": "Composição das Subfunções da Educação",
            "descricao": "Detalhamento de onde o dinheiro da Educação foi aplicado — Todas as Capitais (2024)",
            "moeda": ["Pago_Total"],
            "n": None,
        },
    ]

    indices = []
    for cfg in configs:
        chave = cfg["chave"]
        if chave not in resultados:
            continue

        df = resultados[chave]
        if df.empty:
            continue

        html_df = _formatar_df(df, cfg["moeda"])
        html_final = TEMPLATE.format(
            titulo=cfg["titulo"],
            descricao=cfg["descricao"],
            tabela=html_df,
        )

        nome_arquivo = f"tabela_{chave}.html"
        caminho = pasta_destino / nome_arquivo
        caminho.write_text(html_final, encoding="utf-8")

        indices.append(
            f'    <li><a href="{nome_arquivo}">{cfg["titulo"]}</a></li>'
        )

    indice_html = _gerar_indice(indices)
    (pasta_destino / "index.html").write_text(indice_html, encoding="utf-8")


def _gerar_indice(itens: list[str]) -> str:
    conteudo = "\n".join(itens)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análises FINBRA — Índice</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #f5f7fa; padding: 60px 20px;
    display: flex; flex-direction: column; align-items: center;
  }}
  .container {{
    max-width: 700px; width: 100%;
    background: white; border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    padding: 40px;
  }}
  h1 {{ font-size: 26px; color: #1a1a2e; margin-bottom: 6px; }}
  .desc {{
    font-size: 14px; color: #666; margin-bottom: 28px;
    border-bottom: 2px solid #e9ecef; padding-bottom: 16px;
  }}
  ul {{ list-style: none; }}
  li {{ margin-bottom: 12px; }}
  a {{
    display: block; padding: 16px 20px;
    background: #f8f9fa; border-radius: 10px;
    color: #1a1a2e; text-decoration: none;
    font-weight: 600; font-size: 16px;
    border-left: 4px solid #1a1a2e;
    transition: background 0.2s, transform 0.1s;
  }}
  a:hover {{ background: #e9ecef; transform: translateX(4px); }}
  .footer {{
    margin-top: 32px; text-align: center; font-size: 12px; color: #999;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 Análises FINBRA</h1>
  <div class="desc">Desafio Sefaz Maceió — Clique em uma análise para visualizar a tabela</div>
  <ul>
{conteudo}
  </ul>
</div>
<div class="footer">Dados: FINBRA/SICONFI — 2020 a 2024</div>
</body>
</html>"""
