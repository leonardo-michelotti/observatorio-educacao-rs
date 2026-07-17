-- Indicadores (formato largo na origem) -> unpivot para formato longo (tidy).
-- As duas famílias vêm das planilhas oficiais do Inep, sem a camada harmonizada intermediária.
with src as (
    select * from read_parquet('data/bronze/indicadores.parquet')
),

-- 1) TAXA DE APROVAÇÃO -------------------------------------------------------
-- O intervalo físico funciona como contrato, não como heurística para corrigir a fonte.
aprovacao as (
    select nivel, ano, 'taxa_aprovacao' as indicador, 'ef_anos_iniciais' as etapa, taxa_aprovacao_ef_anos_iniciais as valor from src
    union all
    select nivel, ano, 'taxa_aprovacao', 'ef_anos_finais', taxa_aprovacao_ef_anos_finais from src
    union all
    select nivel, ano, 'taxa_aprovacao', 'em',             taxa_aprovacao_em             from src
),
aprovacao_valida as (
    select * from aprovacao where valor between 0 and 100
),

-- 2) DISTORÇÃO IDADE-SÉRIE -------------------------------------------------
tdi as (
    select nivel, ano, 'distorcao_idade_serie' as indicador, 'ef_anos_iniciais' as etapa, tdi_ef_anos_iniciais as valor from src
    union all
    select nivel, ano, 'distorcao_idade_serie', 'ef_anos_finais', tdi_ef_anos_finais from src
    union all
    select nivel, ano, 'distorcao_idade_serie', 'em',             tdi_em             from src
),
tdi_valida as (
    select * from tdi
    where valor between 0 and 100
)

select nivel, ano, indicador, etapa, valor from aprovacao_valida
union all
select nivel, ano, indicador, etapa, valor from tdi_valida
