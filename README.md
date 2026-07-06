# Analise da Execucao Orcamentaria das Capitais Brasileiras

## Objetivo

Investigar como as 26 capitais brasileiras executam o orcamento publico — de tudo que e *empenhado* (comprometido), quanto realmente e *pago*. A analise se aprofunda no caso de **Natal**, que apresenta a menor taxa de execucao, para entender se o problema e local ou estrutural.

**Pergunta norteadora:** Existe diferenca relevante entre o que as capitais prometem gastar e o que de fato pagam? Esse padrao e uniforme entre areas (funcoes) ou concentrado em algumas?

## Base de dados

- **Fonte:** FINBRA/Siconfi — Despesas por Funcao (Anexo I-E)
- **Periodo:** 2020-2024 (2025 excluido — dados incompletos)
- **Escopo:** 26 capitais brasileiras, 27 funcoes de governo
- **Indicador principal:** `Taxa de Execucao = (Despesas Pagas / Despesas Empenhadas) x 100`

## Tecnologias utilizadas

- **Python 3** + **venv**
- **DuckDB** — Consultas SQL analiticas
- **Pandas** — Manipulacao de dados
- **Matplotlib** — Visualizacoes
- **PyArrow/Parquet** — Armazenamento

## Estrutura do projeto

```
Desafio-Analista-de-Dados-Sefaz-Macei-
├── requirements.txt
├── notebooks/
│   ├── 1-Preparar_Dataset.ipynb   # ETL (rodar primeiro)
│   └── 2-Analise.ipynb            # Analise completa
├── src/
│   ├── banco/
│   │   ├── conexao_duckdb.py
│   │   └── criar_tabela.py
│   └── utils/
│       └── constantes.py
├── dados_compactos/
├── dados_extraidos/
├── data/processed/
└── finbra.duckdb
```

## Etapas da analise

### 1. Consolidacao dos arquivos
Descompactar ZIPs por ano, ler CSVs (latin-1, `;`, decimal `,`), adicionar coluna `Ano` e classificar `ContaTipo` (Funcao, Subfuncao, Subfuncao_agregada, Total_Geral).

### 2. Armazenamento no DuckDB
Salvar consolidado em Parquet e carregar tabela `despesas_finbra` no DuckDB.

### 3. Calculo da taxa de execucao
`Taxa = (Pago / Empenhado) * 100` por capital e por funcao (702 registros: 26 capitais x 27 funcoes).

### 4. Ranking de execucao em Saude e Educacao
Identificar as capitais com melhor e pior desempenho nas duas funcoes mais relevantes.

### 5. Investigacao do caso de Natal
Natal apresenta a menor taxa de execucao tanto em Saude (83,34%) quanto em Educacao (78,01%). A investigacao busca entender por que.

### 6. Comparacao com a media nacional
Comparar a taxa de execucao de Natal por funcao com a media das 26 capitais para identificar onde Natal esta mais abaixo da media.

### 7. Investigacao por subfuncoes
Aprofundar nas subfuncoes de Natal para encontrar os vetores que puxam a taxa para baixo.

### 8. Validacao se o problema era local ou estrutural
Verificar se a baixa execucao em funcoes criticas (Urbanismo e Habitacao) e um problema exclusivo de Natal ou um padrao nacional.

## Principais descobertas

### Ranking em Saude (2020-2024)

| Posicao | Capital | Taxa |
|---------|---------|------|
| 1 | Recife | 98,97% |
| 2 | Porto Velho | 98,64% |
| 3 | Belem | 98,63% |
| 4 | **Maceio** | **97,91%** |
| 25 | Belo Horizonte | 86,86% |
| 26 | **Natal** | **83,34%** |

### Ranking em Educacao (2020-2024)

| Posicao | Capital | Taxa |
|---------|---------|------|
| 1 | Fortaleza | 97,03% |
| 2 | Boa Vista | 96,98% |
| 3 | Salvador | 96,43% |
| 15 | **Maceio** | **89,66%** |
| 25 | Sao Luis | 78,33% |
| 26 | **Natal** | **78,01%** |

### Natal vs media das capitais (por funcao)

Natal esta abaixo da media em **9 de 15 funcoes** analisadas. Maiores quedas:

| Funcao | Natal | Media | Diferenca |
|--------|-------|-------|-----------|
| Habitacao | 65,87% | 84,99% | -19,12 pp |
| Urbanismo | 73,83% | 86,27% | -12,43 pp |
| Educacao | 78,01% | 90,28% | -12,27 pp |
| Comercio e Servicos | 73,16% | 85,15% | -11,99 pp |
| Encargos Especiais | 86,90% | 97,58% | -10,68 pp |
| Saude | 83,34% | 93,26% | -9,91 pp |

### Subfuncoes que puxam Natal para baixo

| Subfuncao | Taxa |
|-----------|------|
| Habitacao Urbana | 21,97% |
| Infraestrutura Urbana | 41,06% |
| Patrimonio Historico | 48,57% |
| Assistencia ao Idoso | 54,71% |
| Suporte Profilatico e Terapeutico | 57,05% |
| Transportes Coletivos Urbanos | 61,19% |

### Verificacao: problema local ou estrutural?

**Conclusao: O problema e local, nao estrutural.**

- **Urbanismo:** Media nacional 86,27%. Natal esta em 73,83% (24o lugar). A maioria das capitais executa acima de 90%.
- **Habitacao:** Media nacional 84,99%. Natal esta em 65,87% (24o lugar). A maioria das capitais executa acima de 80%.

Natal aparece de forma consistente entre os piores desempenhos do ranking nas duas funcoes. O problema nao esta nas funcoes em si (que nacionalmente tem execucao elevada), mas na **capacidade de execucao orcamentaria especifica de Natal** nessas areas.

## Como executar

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install notebook        # Jupyter Notebook (necessario para rodar os notebooks)

# Preparar dataset (primeira vez)
jupyter notebook notebooks/1-Preparar_Dataset.ipynb

# Rodar analise
jupyter notebook notebooks/2-Analise.ipynb
```

> **Nota:** Se o comando `jupyter` nao for reconhecido, execute `pip install notebook` antes de tentar novamente. Para facilitar a execucao dos notebooks, instale a extensao **Jupyter** no VS Code (busque por "Jupyter" nas extensoes e instale a da Microsoft).

## Consideracoes finais

- **Desvio padrao amostral** (n-1): Trabalhamos com amostra de 26 capitais
- **Padrao identificado:** A baixa execucao de Natal e concentrada em funcoes de investimento e desenvolvimento urbano (Urbanismo e Habitacao), enquanto areas de manutencao de servicos essenciais (Legislativa, Previdencia, Seguranca Publica) apresentam desempenho proximo ou acima da media
