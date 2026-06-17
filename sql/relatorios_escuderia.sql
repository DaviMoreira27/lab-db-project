-- Relatórios 4 e 5 da escuderia.

-- Todas recebem o id da escuderia logada e filtram por ele, já que uma
-- escuderia só pode ver os próprios dados.


-- Relatório 4. Lista cada piloto que correu pela escuderia, pelo nome
-- completo, e quantas vezes ele venceu correndo POR ELA. A vitória conta
-- dentro do constructor_id, então um piloto que ganhou por outra equipe
-- aparece com zero aqui. Quem correu pela escuderia mas nunca venceu também
-- aparece na lista, com zero vitórias.
CREATE OR REPLACE FUNCTION get_constructor_drivers_wins(p_constructor_id INT)
RETURNS TABLE(
    piloto     TEXT,
    vitorias   BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (d.given_name || ' ' || d.family_name)::TEXT       AS piloto,
        COUNT(*) FILTER (WHERE res.position = '1')         AS vitorias
    FROM results res
    JOIN drivers d ON d.id = res.driver_id
    WHERE res.constructor_id = p_constructor_id
    GROUP BY d.id, d.given_name, d.family_name
    ORDER BY COUNT(*) FILTER (WHERE res.position = '1') DESC,
             d.family_name, d.given_name;
END;
$$ LANGUAGE plpgsql;


-- Relatório 5.
-- É a mesma contagem de resultados por status que o admin e o piloto fazem
-- só que olhando apenas os resultados da escuderia logada.
CREATE OR REPLACE FUNCTION get_constructor_status_count(p_constructor_id INT)
RETURNS TABLE(
    status       TEXT,
    quantidade   BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.status::TEXT     AS status,
        COUNT(*)           AS quantidade
    FROM results res
    JOIN status s ON s.id = res.status_id
    WHERE res.constructor_id = p_constructor_id
    GROUP BY s.status
    ORDER BY COUNT(*) DESC, s.status;
END;
$$ LANGUAGE plpgsql;
