-- =============================================================================
-- RELATÓRIO 2 — View materializada de aeroportos próximos a cidades brasileiras
-- =============================================================================
--
-- Por que view materializada e não query direta?
--
-- A fórmula haversine envolve funções trigonométricas (asin, sqrt, power,
-- radians, cos) aplicadas linha a linha para cada par (cidade × aeroporto).
-- Executada como query direta a cada chamada, esse cálculo é repetido do zero
-- sempre que o usuário busca uma cidade — mesmo que os dados subjacentes
-- (airports, cities) não tenham mudado.
--
-- airports e cities são tabelas de referência: aeroportos raramente são
-- inseridos ou alterados, e o cadastro de cidades é praticamente imutável após
-- a carga inicial. Isso torna o custo de REFRESH MATERIALIZED VIEW desprezível
-- na prática (executado apenas quando um novo aeroporto é cadastrado).
--
-- Com a view materializada, o haversine é computado uma única vez para todos
-- os pares válidos (cidade brasileira → aeroporto brasileiro ≤ 100 km, tipo
-- medium ou large). A query parametrizada do relatório passa a ser um simples
-- SELECT com filtro por nome — sem nenhum cálculo trigonométrico em tempo de
-- execução, acesso via index scan no índice funcional abaixo.
--
-- Tradeoff escrita vs leitura:
--   Escrita  — REFRESH bloqueia leituras concorrentes se executado sem
--              CONCURRENTLY. Para este caso de uso (baixíssima frequência de
--              atualização), isso é aceitável. Se necessário, usar
--              REFRESH MATERIALIZED VIEW CONCURRENTLY após criar um índice
--              único na view.
--   Leitura  — acesso em O(log n) via índice funcional no nome da cidade,
--              sem custo trigonométrico.
--   Espaço   — armazena apenas os pares válidos (cidade + aeroporto dentro
--              de 100 km), que são uma fração pequena do produto cartesiano
--              total.

-- ADM1	first-order administrative division	a primary administrative division of a country, such as a state in the United States
-- admin1_code é o código da unidade federativa (UF) no GeoNames — "SP", "RJ",
-- "SC" etc. Incluído para distinguir cidades homônimas: "Campinas" existe como
-- nome em múltiplos estados; sem esse campo a view misturaria os aeroportos de
-- todas elas numa única chave de agrupamento.
-- https://www.geonames.org/BR/administrative-division-brazil.html
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aeroportos_cidades_br AS
SELECT
    ci.name          AS cidade_pesquisada,
    ci.admin1_code   AS estado,
    a.iata_code,
    a.name           AS aeroporto,
    ci_ap.name       AS cidade_aeroporto,
    ROUND((
        6371 * 2 * asin(sqrt(
            power(sin(radians((a.latitude_deg - ci.latitude) / 2)), 2) +
            cos(radians(ci.latitude)) * cos(radians(a.latitude_deg)) *
            power(sin(radians((a.longitude_deg - ci.longitude) / 2)), 2)
        ))
    )::numeric, 1) AS distancia_km,
    at.type          AS tipo
FROM cities ci
JOIN countries co    ON ci.country_id     = co.id   AND co.code  = 'BR'
JOIN airport_types at ON at.type IN ('medium_airport', 'large_airport')
JOIN airports a      ON a.airport_type_id = at.id
    AND (
        6371 * 2 * asin(sqrt(
            power(sin(radians((a.latitude_deg - ci.latitude) / 2)), 2) +
            cos(radians(ci.latitude)) * cos(radians(a.latitude_deg)) *
            power(sin(radians((a.longitude_deg - ci.longitude) / 2)), 2)
        ))
    ) <= 100
JOIN cities ci_ap   ON a.city_id          = ci_ap.id
JOIN countries co2  ON ci_ap.country_id   = co2.id  AND co2.code = 'BR'
ORDER BY ci.name, ci.admin1_code, distancia_km;

-- Índice funcional na coluna cidade_pesquisada (case-insensitive).
-- Permite que WHERE LOWER(cidade_pesquisada) = LOWER($1) use index scan
-- em vez de sequential scan na view materializada.
CREATE INDEX IF NOT EXISTS idx_mv_aeroportos_cidade
    ON mv_aeroportos_cidades_br(LOWER(cidade_pesquisada));

-- =============================================================================
-- TRIGGER — Refresh automático da view materializada ao inserir aeroporto
-- =============================================================================
--
-- O REFRESH é disparado AFTER INSERT, FOR EACH STATEMENT — não FOR EACH ROW.
-- Se um batch de aeroportos for inserido em um único INSERT, o refresh ocorre
-- uma única vez ao final do statement, evitando reconstruções desnecessárias.
--
-- O REFRESH sem CONCURRENTLY adquire lock exclusivo na view durante a
-- reconstrução, bloqueando leituras concorrentes. Para este caso de uso
-- (inserções raríssimas, dashboard consultado por um admin), isso é aceitável.
-- Se no futuro a tabela airports receber cargas frequentes, substituir por
-- REFRESH MATERIALIZED VIEW CONCURRENTLY — o que requer um índice UNIQUE na
-- view (adicionar sobre cidade_pesquisada + aeroporto, por exemplo).
--
-- O trigger cobre apenas INSERT. UPDATE e DELETE em airports são operações
-- ainda mais raras e podem exigir refresh manual se ocorrerem.

CREATE OR REPLACE FUNCTION fn_refresh_mv_aeroportos()
RETURNS trigger AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_aeroportos_cidades_br;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_refresh_mv_aeroportos
AFTER INSERT ON airports
FOR EACH STATEMENT
EXECUTE FUNCTION fn_refresh_mv_aeroportos();
