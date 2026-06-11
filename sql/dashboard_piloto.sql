-- Função: retorna o primeiro e último ano em que há dados do piloto na tabela RESULTS
-- Recebe o driver_id como parâmetro (id_original da sessão do piloto logado)
CREATE OR REPLACE FUNCTION get_driver_years(p_driver_id INT)
RETURNS TABLE(primeiro_ano INT, ultimo_ano INT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        MIN(EXTRACT(YEAR FROM r.race_date)::INT) AS primeiro_ano,
        MAX(EXTRACT(YEAR FROM r.race_date)::INT) AS ultimo_ano
    FROM results res
    JOIN races r ON r.id = res.race_id
    WHERE res.driver_id = p_driver_id;
END;
$$ LANGUAGE plpgsql;

-- Função: retorna pontos, vitórias e total de corridas por ano e circuito para um piloto
-- position = '1' indica vitória
CREATE OR REPLACE FUNCTION get_driver_stats(p_driver_id INT)
RETURNS TABLE(
    ano        INT,
    circuito   TEXT,
    pontos     NUMERIC,
    vitorias   BIGINT,
    corridas   BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        EXTRACT(YEAR FROM r.race_date)::INT     AS ano,
        c.name                                  AS circuito,
        SUM(res.points)                         AS pontos,
        COUNT(*) FILTER (WHERE res.position = '1') AS vitorias,
        COUNT(*)                                AS corridas
    FROM results res
    JOIN races    r ON r.id    = res.race_id
    JOIN circuits c ON c.id   = r.circuit_id
    WHERE res.driver_id = p_driver_id
    GROUP BY ano, c.name
    ORDER BY ano, c.name;
END;
$$ LANGUAGE plpgsql;

