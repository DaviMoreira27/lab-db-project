-- Dashboard da escuderia.

-- O filtro por constructor_id se repete nas funções, então ele precisa de índice.
-- O idx_results_constructor_id já existe (foi criado no relatorios_admin.sql pro relatório do admin), então só reaproveito.
-- Criei o composto (constructor_id, driver_id) porque o dashboard conta pilotos distintos e o relatório 4 agrupa por piloto com as duas colunas
-- no mesmo índice o banco já pega as linhas da escuderia ordenadas por piloto e não precisa reordenar pra fazer o COUNT(DISTINCT) e o GROUP BY.
-- Falta medir com EXPLAIN ANALYZE antes de afirmar o ganho no relatório.

CREATE INDEX IF NOT EXISTS idx_results_constructor_driver
    ON results USING BTREE (constructor_id, driver_id);


-- Devolve numa linha só os números que aparecem na tela:
-- nome, quantos pilotos diferentes já correram pela equipe, quantas vitórias ela teve e em que ano começa e termina o histórico dela na base.
-- O qtd_pilotos é o mesmo de "pilotos associados"
-- Usei LEFT JOIN de propósito, se uma escuderia não tiver nenhum resultado, ainda assim volta uma linha com zeros em vez de não voltar nada.
CREATE OR REPLACE FUNCTION get_constructor_dashboard(p_constructor_id INT)
RETURNS TABLE(
    escuderia      TEXT,
    qtd_pilotos    BIGINT,
    qtd_vitorias   BIGINT,
    primeiro_ano   INT,
    ultimo_ano     INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.name::TEXT                                       AS escuderia,
        COUNT(DISTINCT res.driver_id)                      AS qtd_pilotos,
        COUNT(*) FILTER (WHERE res.position = '1')         AS qtd_vitorias,
        MIN(EXTRACT(YEAR FROM r.race_date))::INT           AS primeiro_ano,
        MAX(EXTRACT(YEAR FROM r.race_date))::INT           AS ultimo_ano
    FROM constructors c
    LEFT JOIN results res ON res.constructor_id = c.id
    LEFT JOIN races   r   ON r.id = res.race_id
    WHERE c.id = p_constructor_id
    GROUP BY c.id, c.name;
END;
$$ LANGUAGE plpgsql;
