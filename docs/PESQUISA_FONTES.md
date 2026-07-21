# Fontes, metodologia e proveniência

O projeto compara indicadores agregados da educação básica em Santa Maria, no Rio Grande do
Sul e no Brasil. A referência institucional é o Instituto Nacional de Estudos e Pesquisas
Educacionais Anísio Teixeira (Inep), mas o caminho de acesso varia por indicador.

## Fontes utilizadas

| Indicadores | Fonte de origem | Acesso usado pelo projeto | Período |
|---|---|---|---|
| Aprovação | Inep | Planilhas anuais oficiais (ZIP com XLS/XLSX) | 2007–2025 |
| Distorção idade-série (TDI) | Inep | Planilhas anuais oficiais (ZIP com XLS/XLSX) | 2006–2025 |
| IDEB e notas SAEB | Inep | `basedosdados.br_inep_ideb` no BigQuery | 2005–2023 |

O recorte municipal usa o código IBGE `4316907` para Santa Maria; o estadual usa `RS`. Para
IDEB e SAEB, a análise seleciona a rede pública, recorte comum aos três níveis geográficos.

## Duas rotas de ingestão

```text
Planilhas INEP ── parser XLS/XLSX ──┐
                                     ├─ Parquet bronze ─ dbt/DuckDB ─ gráficos e páginas
Base dos Dados / BigQuery ──────────┘
```

`ingestion/extract_inep.py` descobre os links nas páginas anuais do Inep, baixa os arquivos,
seleciona semanticamente as colunas das três etapas e grava aprovação e TDI em
`data/bronze/indicadores.parquet`. Para cada ZIP, registra URL, ano, escopo, tamanho e SHA-256
em `data/bronze/inep_provenance.json`.

Alguns arquivos históricos são servidos sem a cadeia intermediária completa. O extrator mantém
a verificação TLS ativa e acrescenta ao pacote Mozilla o certificado intermediário publicado
pela autoridade indicada no próprio certificado do Inep. Não há uso de `verify=False`.

`ingestion/extract_bd.py` consulta IDEB e seus componentes SAEB no BigQuery e grava
`data/bronze/ideb.parquet`. Como essa rota ainda depende de uma camada harmonizada e de
credenciais externas, o workflow de atualização oficial também pode reconstruir esse bronze a
partir do snapshot auditado embutido no painel versionado, usando
`ingestion/load_ideb_snapshot.py`. O mesmo carregador restaura o histórico publicado de
aprovação/TDI antes do upsert do último ano direto. O snapshot evita consultas e downloads
legados; ele não muda a fonte nem cria observações novas.

## Transformação e contrato analítico

Os modelos de staging normalizam tipos, níveis e etapas. O mart `fct_indicadores` usa o grão:

```text
(indicador, nível geográfico, etapa, ano) → valor
```

Os testes verificam campos obrigatórios, categorias aceitas, unicidade do grão e faixas físicas
dos indicadores. O parser direto também confronta referências oficiais de 2025. Nenhuma etapa
interpola, estima ou corrige manualmente valores publicados.

## Regras de visualização

- Uma etapa entra no gráfico quando pelo menos dois níveis geográficos possuem cinco ou mais
  anos válidos.
- Somente as séries que cumprem esse mínimo são desenhadas.
- Anos iniciais, anos finais e Ensino Médio são recortes agregados distintos; sua comparação
  não acompanha a mesma coorte de estudantes.
- As diferenças apresentadas são descritivas. Não permitem atribuir causalidade, avaliar alunos
  individualmente ou isolar o efeito de uma política pública.

## Limitações conhecidas

A auditoria encontrou valores incompatíveis na tabela harmonizada de indicadores educacionais
antes usada para rendimento e TDI. Por isso, esses dois grupos agora vêm diretamente das
planilhas oficiais. IDEB e SAEB continuam temporariamente via Base dos Dados/BigQuery; migrá-los
para arquivos oficiais diretos é a pendência de fonte ainda aberta.

O histórico publicado pode sofrer revisões pelo próprio Inep. Os hashes permitem identificar
qual arquivo foi processado, mas não impedem que a origem publique uma nova versão. Dados
brutos, credenciais e o banco DuckDB local são deliberadamente excluídos do Git.

## Como reproduzir

As ingestões estão em `ingestion/`, as transformações em `dbt/models/`, os testes em
`dbt/tests/` e `tests/`, e as instruções operacionais em [`COMO_RODAR.md`](COMO_RODAR.md). O
workflow de atualização só propõe mudanças por pull request; CI e revisão precedem o merge e a
publicação.
