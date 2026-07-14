# Fontes e proveniência dos dados

Este projeto analisa a educação básica em Santa Maria, no Rio Grande do Sul e no Brasil.
Os indicadores são publicados pelo Instituto Nacional de Estudos e Pesquisas Educacionais
Anísio Teixeira (Inep) e consultados por meio das tabelas harmonizadas da Base dos Dados no
BigQuery.

## Fontes utilizadas

| Fonte | Uso no projeto |
|---|---|
| [Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos) | Fonte oficial do IDEB, SAEB, taxas de rendimento e distorção idade-série |
| [Base dos Dados](https://basedosdados.org/) | Camada de acesso e harmonização usada pela ingestão |
| [IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php) | Identificação territorial de Santa Maria e do Rio Grande do Sul |

As tabelas consultadas são:

- `basedosdados.br_inep_ideb`;
- `basedosdados.br_inep_indicadores_educacionais`.

O recorte municipal usa o código IBGE `4316907` para Santa Maria. O recorte estadual usa a
sigla `RS`.

## Fluxo de proveniência

```text
Inep → Base dos Dados / BigQuery → Parquet bronze → dbt / DuckDB → gráficos e páginas
```

A ingestão preserva os valores consultados em arquivos Parquet locais, que não são
versionados. As transformações e regras de qualidade ficam nos modelos dbt do repositório. Os
gráficos e as páginas publicadas são derivados do modelo analítico `fct_indicadores`.

## Limitações conhecidas

A auditoria identificou valores historicamente inconsistentes em partes da tabela harmonizada
`br_inep_indicadores_educacionais`. Por isso, o projeto aplica regras explícitas de curadoria e
publica apenas séries que passaram pelas verificações documentadas no README e nos modelos dbt.

Essas regras não corrigem a fonte. Elas evitam apresentar como válidos pontos incompatíveis
com as séries oficiais e tornam as exclusões auditáveis no código.

## Reprodutibilidade

As consultas estão em `ingestion/extract_bd.py`, as transformações em `dbt/models/` e as
instruções de execução em [`COMO_RODAR.md`](COMO_RODAR.md). Credenciais, dados brutos e o banco
DuckDB local são deliberadamente excluídos do Git.
