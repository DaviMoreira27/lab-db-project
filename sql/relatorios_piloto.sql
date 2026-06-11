- Relatório
-- B-tree, sem dúvida. Aqui o raciocínio:
-- O relatório faz três coisas que favorecem B-tree:
-- Filtro por driver_id — equivalência (WHERE driver_id = ?). Hash também serviria aqui.
-- Agrupamento/ordenação por ano — envolve GROUP BY e ORDER BY em race_date. Hash não suporta range/ordenação, B-tree sim.
-- Join results.race_id → races.id — B-tree é o padrão para FK joins.
-- Hash só ganha em equivalência pura e isolada. Aqui tem ordenação envolvida, então B-tree é a escolha certa.

-- Índice em results(driver_id) para filtrar rapidamente os resultados do piloto logado
CREATE INDEX IF NOT EXISTS idx_results_driver_id 
    ON results USING BTREE (driver_id);

-- Índice em results(race_id) para otimizar o join com races
CREATE INDEX IF NOT EXISTS idx_results_race_id 
    ON results USING BTREE (race_id);

-- Índice em races(race_date) para extração do ano e ordenação
CREATE INDEX IF NOT EXISTS idx_races_race_date 
    ON races USING BTREE (race_date);

-- Relatório 6: pontos por ano com corridas detalhadas, restrito ao piloto logado
CREATE OR REPLACE FUNCTION get_driver_points_by_year(p_driver_id INT)
RETURNS TABLE(
    ano         INT,
    corrida     TEXT,
    data        DATE,
    pontos      NUMERIC,
    total_ano   NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        EXTRACT(YEAR FROM r.race_date)::INT         AS ano,
        r.race_name                                 AS corrida,
        r.race_date                                 AS data,
        res.points                                  AS pontos,
        SUM(res.points) OVER (
            PARTITION BY EXTRACT(YEAR FROM r.race_date)
        )                                           AS total_ano
    FROM results res
    JOIN races r ON r.id = res.race_id
    WHERE res.driver_id = p_driver_id
      AND res.points > 0
    ORDER BY ano, r.race_date;
END;
$$ LANGUAGE plpgsql;


-- Relatório 7: contagem de resultados por status, restrito ao piloto logado
CREATE OR REPLACE FUNCTION get_driver_status_count(p_driver_id INT)
RETURNS TABLE(
    status     TEXT,
    quantidade BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.status        AS status,
        COUNT(*)        AS quantidade
    FROM results res
    JOIN status s ON s.id = res.status_id
    WHERE res.driver_id = p_driver_id
    GROUP BY s.status
    ORDER BY quantidade DESC;
END;
$$ LANGUAGE plpgsql;