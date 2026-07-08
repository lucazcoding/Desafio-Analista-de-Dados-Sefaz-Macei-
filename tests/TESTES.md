# Testes — Pipeline FINBRA/Siconfi

Este documento descreve os testes de sanidade criados na Etapa 3 (validação),
o que cada um verifica, por que ele existe, e como rodá-los localmente.

Os testes cobrem as funções extraídas na Etapa 2 (modularização) — não
alteram nem redefinem nenhuma regra de negócio da análise original, apenas
validam que o pipeline continua se comportando como esperado.

## Como rodar

```bash
.\venv\Scripts\pytest tests\test_transform.py -v
```

> ⚠️ **Importante — conflito de conexão com o DuckDB**
> O DuckDB permite apenas **uma conexão de escrita por vez** no mesmo arquivo
> `.duckdb`. Se você tiver o notebook `2-Analise.ipynb` aberto no Jupyter com
> a conexão (`con`) ainda ativa, os testes vão falhar com um erro de lock
> (`IOException` / `database is locked`), porque a fixture `con` do
> `test_transform.py` tenta abrir uma **segunda** conexão no mesmo arquivo.
>
> **Antes de rodar os testes**, sempre execute `con.close()` na última célula
> do notebook (ou reinicie o kernel) para liberar o arquivo `.duckdb`. Essa
> exigência não é um bug do teste — é uma característica do próprio DuckDB
> (diferente do SQLite, que tolera múltiplos leitores/gravadores com mais
> flexibilidade).

## Pré-requisitos para rodar os testes

Os testes **não são unitários puros** — as fixtures `df_raw` e `con` leem
arquivos já processados em disco (`finbra_consolidado.parquet` e
`finbra.duckdb`). Isso significa que, antes de rodar `pytest`, o notebook
`1-Preparar_Dataset.ipynb` precisa já ter sido executado ao menos uma vez,
gerando esses dois arquivos.

Se você clonar o repositório do zero e rodar `pytest` direto, vai dar erro
de arquivo não encontrado — isso é esperado, não é falha do teste.

---

## Testes de integração (usam os dados reais processados)

### 1. `test_valor_e_numerico`

**O que verifica:** que a coluna `Valor`, depois de toda a transformação
(conversão de decimal `,` → `.`), está com tipo numérico (`float`/`int`),
e não como texto.

**Por que importa:** se essa coluna ficasse como `string` por algum motivo
(ex.: falha silenciosa na conversão de um CSV com formatação diferente),
qualquer soma ou média calculada depois estaria completamente errada, sem
necessariamente dar erro visível — o pandas soma strings concatenando, o
que gera bugs difíceis de perceber a olho nu.

---

### 2. `test_sem_duplicatas_chave`

**O que verifica:** que não existem duas linhas idênticas para a mesma
combinação de `Instituição`, `Conta`, `Coluna` e `Ano`.

**Por que importa:** esse é o nível de granularidade esperado do dataset
(uma linha = uma capital + uma conta orçamentária + um tipo de despesa +
um ano). Duplicatas nessa chave inflariam artificialmente qualquer soma ou
indicador — por exemplo, uma taxa de execução calculada sobre dado
duplicado ficaria estatisticamente distorcida sem nenhum erro aparente.

---

### 3. `test_soma_subfuncoes_igual_funcao`

**O que verifica:** que, para cada combinação de `Instituição` + `Ano` +
`Coluna` (Pagas/Empenhadas), a soma dos valores das subfunções bate com o
valor total declarado da função-mãe, com tolerância de `0.01` (arredondamento).

**Como funciona:**
- Extrai o código de 2 dígitos da função (`"10 - Saúde"` → `10`) e das
  subfunções (`"10.301 - Atenção Básica"` → `10`).
- Soma **duas** categorias de conta: `Subfunção` (detalhamento normal) e
  `Subfuncao_agregada` (contas do tipo `"FU26 - Demais Subfunções"`, onde o
  ente federativo agrupou parte do gasto sem detalhar por subfunção
  específica).
- Compara a soma com o total da função e reporta qualquer diferença acima
  de 1 centavo.

**Por que soma as duas categorias — histórico do achado:**
Na primeira versão deste teste, apenas `ContaTipo = 'Subfunção'` era somado.
Isso gerou **2.444 divergências**, algumas de milhões de reais (ex.: Rio
Branco-AC, 2020, função Transporte: diferença de R$ 14.936.413,67).

Investigação identificou que essas diferenças eram inteiramente explicadas
por contas `Subfuncao_agregada` não capturadas pela query original —
exemplo real encontrado:

| Conta | ContaTipo | Valor |
|---|---|---|
| `26 - Transporte` | Função | R$ 16.059.901,07 |
| `26.782 - Transporte Rodoviário` | Subfunção | R$ 1.123.487,40 |
| `FU26 - Demais Subfunções` | Subfuncao_agregada | R$ 14.936.413,67 |

`1.123.487,40 + 14.936.413,67 = 16.059.901,07` — bate exatamente com o
total da função. Ou seja, **não era erro nos dados nem no pipeline** — era
uma lacuna na regra de reconciliação do teste, que não previa essa
categoria. A query foi corrigida para incluir `Subfuncao_agregada` na soma.

**Por que importa:** esse é o teste mais importante do conjunto — ele
valida a integridade estrutural real dos dados públicos (que a hierarquia
função → subfunção soma corretamente), e o processo de investigação da
falha serviu para entender melhor a própria classificação orçamentária do
FINBRA/Siconfi.

---

### 4. `test_anos_no_intervalo_valido`

**O que verifica:** que todo valor da coluna `Ano` está entre 2020 e 2025
(inclusive), conforme o escopo definido para o desafio.

**Por que importa:** protege contra erro de extração de ano a partir do
caminho do arquivo (função `descobrir_ano`) — por exemplo, se um CSV
acabasse em uma pasta com nome errado, isso entraria como um ano fora do
escopo e distorceria qualquer análise de série temporal.

---

## Testes unitários (não dependem de dados em disco)

Esses testes usam dados fictícios criados na hora (`pd.DataFrame(...)`) e
validam o comportamento das funções isoladamente, sem depender do parquet
ou do DuckDB já existirem.

### `TestClassificarConta`

Valida a função `classificar_conta`, responsável por identificar o nível de
agregação de uma conta a partir do texto:

| Entrada | Resultado esperado | O que representa |
|---|---|---|
| `"Despesas Exceto Intraorçamentárias"` | `Total_Geral` | Total consolidado |
| `"Despesas Intraorçamentárias"` | `Total_Geral` | Total consolidado (intra) |
| `"10 - Saúde"` | `Função` | Função orçamentária |
| `"10.301 - Atenção Básica"` | `Subfunção` | Subfunção detalhada |
| `"FU10 - Demais Subfunções"` | `Subfuncao_agregada` | Subfunções não detalhadas |
| `None` / `42` (não-string) | `Outros` | Entrada inesperada, tratada com segurança |

O último caso (`None`/`42`) garante que a função não quebra com dado
malformado — em vez de lançar exceção, classifica como `Outros`, permitindo
que o pipeline continue e o problema seja investigado depois, se necessário.

### `TestDescobrirAno`

Valida a função `descobrir_ano`, que extrai o ano a partir do caminho do
arquivo (ex.: `.../2022/finbra.csv` → `2022`):

- **Caso de sucesso:** pasta com nome de ano válido no caminho → ano
  extraído corretamente.
- **Caso de erro:** pasta sem nenhum ano identificável no caminho → a
  função deve levantar `ValueError` com mensagem `"Ano não encontrado"`,
  em vez de falhar silenciosamente ou retornar um valor arbitrário.

### `TestLimparTransformarDf`

Valida `limpar_e_transformar_df`, que aplica a limpeza e classificação a um
DataFrame bruto:

- `test_valor_e_numerico_apos_transformacao`: confirma que a coluna `Valor`
  permanece numérica após a transformação.
- `test_coluna_ano_preenchida`: confirma que a coluna `Ano` é preenchida
  corretamente com o valor passado como parâmetro para todas as linhas.
- `test_conta_tipo_classificado`: confirma que, ao processar um DataFrame
  com uma conta de função e uma de subfunção, cada linha recebe o
  `ContaTipo` correto (`Função` / `Subfunção`).

> **Nota de melhoria futura:** o teste `test_valor_e_numerico_apos_
> transformacao` cria a coluna `Valor` já como string decimal brasileira
> (`"1.234,56"`) mas em seguida a sobrescreve manualmente com floats antes
> de chamar a função — então, hoje, ele não valida de fato a conversão de
> string para número, só confirma que um float continua float. Se
> `limpar_e_transformar_df` for responsável por essa conversão em algum
> momento, vale reescrever esse teste passando a string diretamente, sem
> sobrescrever.

---

## Resumo de cobertura

| Teste | Tipo | Depende de dados em disco? |
|---|---|---|
| `test_valor_e_numerico` | Integração | Sim (parquet) |
| `test_sem_duplicatas_chave` | Integração | Sim (parquet) |
| `test_soma_subfuncoes_igual_funcao` | Integração | Sim (DuckDB) |
| `test_anos_no_intervalo_valido` | Integração | Sim (parquet) |
| `TestClassificarConta` (6 casos) | Unitário | Não |
| `TestDescobrirAno` (2 casos) | Unitário | Não |
| `TestLimparTransformarDf` (3 casos) | Unitário | Não |

**Total: 15 testes** (4 de integração + 11 unitários).