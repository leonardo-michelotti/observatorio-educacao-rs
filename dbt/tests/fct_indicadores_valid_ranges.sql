-- Faixas físicas do contrato final. Regras editoriais mais específicas ficam no staging.
select *
from {{ ref('fct_indicadores') }}
where
    (indicador = 'ideb' and valor not between 0 and 10)
    or (
        indicador in ('taxa_aprovacao', 'distorcao_idade_serie')
        and valor not between 0 and 100
    )
    or (
        indicador in ('saeb_matematica', 'saeb_lingua_portuguesa')
        and valor not between 0 and 500
    )
