-- dashboard e relatórios 4 e 5.

-- Todas recebem o id da escuderia logada e filtram por ele, já que uma
-- escuderia só pode ver os próprios dados.


-- O filtro por constructor_id se repete nas três funções, então ele precisa de índice. 
-- O idx_results_constructor_id já existe (foi criado no relatorios_admin.sql pro relatório do admin), então só reaproveito.
-- Criei o composto (constructor_id, driver_id) porque o dashboard conta pilotos distintos e o relatório 4 agrupa por piloto com as duas colunas
-- no mesmo índice o banco já pega as linhas da escuderia ordenadas por piloto e não precisa reordenar pra fazer o COUNT(DISTINCT) e o GROUP BY.
-- Falta medir com EXPLAIN ANALYZE antes de afirmar o ganho no relatório.

CREATE INDEX IF NOT EXISTS idx_results_constructor_driver
    ON results USING BTREE (constructor_id, driver_id);


-- Dashboard da escuderia. Devolve numa linha só os números que aparecem na tela:
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