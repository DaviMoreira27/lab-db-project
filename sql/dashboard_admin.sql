-- =============================================================================
-- ÍNDICES
-- =============================================================================
--
-- PostgreSQL não cria índices automaticamente em colunas de chave estrangeira —
-- apenas PKs são indexadas por padrão. Sem índice, o planner executa sequential
-- scan na tabela inteira a cada JOIN ou filtro. Para tabelas com dezenas de
-- milhares de linhas (results, standings) isso aumenta significativamente o
-- custo de leitura.
--
-- Tradeoff geral de índices B-tree:
--   Leitura  — acesso em O(log n) em vez de O(n). O ganho é proporcional ao
--              volume da tabela e à seletividade do predicado.
--   Escrita  — cada INSERT/UPDATE/DELETE na tabela precisa atualizar o índice,
--              adicionando custo de I/O e manutenção de página. Para tabelas de
--              fatos como results (append-only na prática) esse custo é baixo.
--   Espaço   — índice B-tree usa em média 30-40 % do tamanho da coluna indexada.
--
-- Os índices abaixo foram escolhidos especificamente para as três views do
-- dashboard. Colunas que só aparecem em SELECT de lista (race_name, points etc.)
-- não recebem índice porque a query retorna o conjunto completo mesmo assim.

-- races.season_id: utilizado no JOIN races → seasons em vw_corridas_temporada_atual.
-- Sem índice o planner varre toda a tabela races (~1 000 linhas) para cada
-- execução da view. Com índice o acesso é direto ao subconjunto da temporada.
CREATE INDEX IF NOT EXISTS idx_races_season_id ON races(season_id);

-- results.race_id: utilizado no LEFT JOIN results em vw_corridas_temporada_atual
-- para calcular MAX(laps) por corrida. Results é a maior tabela do schema
-- (~25 000 linhas, ~20 pilotos × ~1 000 corridas). Sem índice cada avaliação
-- da view executa sequential scan completo nessa tabela.
CREATE INDEX IF NOT EXISTS idx_results_race_id ON results(race_id);

-- standings(season_id, round): índice composto utilizado em vw_escuderias_temporada_atual
-- e vw_pilotos_temporada_atual. Ambas as views filtram primeiro por season_id e
-- depois por round = MAX(round). Um índice composto (season_id, round) satisfaz
-- os dois predicados em um único index scan e permite que o subquery
-- MAX(round) também seja resolvido via index-only scan — sem tocar nas páginas
-- de heap da tabela. A ordem das colunas importa: season_id vem primeiro porque
-- é o filtro de maior seletividade (reduz o conjunto de ~N rounds para 1 temporada).
CREATE INDEX IF NOT EXISTS idx_standings_season_round ON standings(season_id, round);

-- constructor_standings.standing_id e driver_standings.standing_id:
-- ambas as tabelas são tabelas de associação (N:1 com standings). O JOIN
-- standings → constructor_standings / driver_standings percorre standing_id
-- como lado "many". Sem índice isso exige sequential scan nas tabelas de
-- associação a cada execução da view. O custo individual é baixo hoje, mas
-- cresce linearmente com a adição de novas temporadas.
CREATE INDEX IF NOT EXISTS idx_constructor_standings_standing_id ON constructor_standings(standing_id);
CREATE INDEX IF NOT EXISTS idx_driver_standings_standing_id ON driver_standings(standing_id);

-- =============================================================================
-- VIEWS
-- =============================================================================
--
-- Por que views regulares e não views materializadas?
--
-- Views materializadas armazenam o resultado fisicamente e tornam a leitura
-- praticamente instantânea (acesso a tabela pré-computada). A contrapartida é
-- que o resultado fica estático até um REFRESH MATERIALIZED VIEW explícito —
-- novas corridas inseridas não aparecem automaticamente.
--
-- Para este dataset (F1 histórico, atualizado poucas vezes por ano) o ganho de
-- latência de uma view materializada seria imperceptível dado o volume (~25k
-- linhas em results). Uma view regular recalcula a cada acesso em milissegundos
-- com os índices acima, e sempre reflete o estado atual do banco sem exigir
-- lógica de refresh na aplicação.
--
-- Se o volume crescer significativamente ou o dashboard for acessado com alta
-- frequência, a migração para MATERIALIZED VIEW é direta: basta trocar
-- CREATE OR REPLACE VIEW por CREATE MATERIALIZED VIEW e adicionar um
-- REFRESH após cada carga de dados.

-- Corridas da temporada mais recente.
-- MAX(res.laps) por corrida porque cada piloto pode ter completado um número
-- diferente de voltas (abandono, safety car etc.); o vencedor normalmente tem
-- o maior valor, que representa as voltas oficiais da prova.
CREATE OR REPLACE VIEW vw_corridas_temporada_atual AS
SELECT
    r.race_name   AS corrida,
    c.name        AS circuito,
    r.race_date   AS data,
    r.race_time   AS horario,
    MAX(res.laps) AS quantidade_voltas
FROM races r
JOIN circuits c ON r.circuit_id = c.id
JOIN seasons s  ON r.season_id  = s.id
LEFT JOIN results res ON res.race_id = r.id
WHERE s.year = (SELECT MAX(year) FROM seasons)
GROUP BY r.id, r.race_name, c.name, r.race_date, r.race_time
ORDER BY r.race_date;

-- Escuderias da temporada mais recente com total de pontos.
-- Usa a tabela standings em vez de agregar results.points porque standings já
-- armazena pontos cumulativos por round — evita re-agregar dezenas de linhas
-- de results por escuderia. O filtro round = MAX(round) garante o standing
-- final da temporada (após a última corrida).
CREATE OR REPLACE VIEW vw_escuderias_temporada_atual AS
SELECT
    c.name    AS escuderia,
    st.points AS total_pontos
FROM constructors c
JOIN constructor_standings cs ON cs.constructor_id = c.id
JOIN standings st             ON cs.standing_id    = st.id
WHERE st.season_id = (SELECT id FROM seasons WHERE year = (SELECT MAX(year) FROM seasons))
  AND st.round = (
      SELECT MAX(round) FROM standings
      WHERE season_id = (SELECT id FROM seasons WHERE year = (SELECT MAX(year) FROM seasons))
  )
ORDER BY st.points DESC;

-- Pilotos da temporada mais recente com total de pontos.
-- Mesma lógica de standings da view de escuderias.
CREATE OR REPLACE VIEW vw_pilotos_temporada_atual AS
SELECT
    d.given_name || ' ' || d.family_name AS piloto,
    st.points                            AS total_pontos
FROM drivers d
JOIN driver_standings ds ON ds.driver_id   = d.id
JOIN standings st        ON ds.standing_id = st.id
WHERE st.season_id = (SELECT id FROM seasons WHERE year = (SELECT MAX(year) FROM seasons))
  AND st.round = (
      SELECT MAX(round) FROM standings
      WHERE season_id = (SELECT id FROM seasons WHERE year = (SELECT MAX(year) FROM seasons))
  )
ORDER BY st.points DESC;
