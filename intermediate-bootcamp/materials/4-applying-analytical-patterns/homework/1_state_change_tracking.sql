WITH seasons AS (
  SELECT MIN(season) AS min_season, MAX(season) - MIN(season) AS total_seasons 
  FROM player_seasons
),
players AS (
  SELECT DISTINCT player_name 
  FROM player_seasons
),
calendar AS (
  SELECT p.player_name, s.min_season + season_offset AS season
  FROM players p
  CROSS JOIN seasons s
  CROSS JOIN generate_series(0, s.total_seasons) season_offset
),
activity AS (
  SELECT player_name, season, 1 AS active 
  FROM player_seasons 
  GROUP BY player_name, season
),
timeline AS (
  SELECT c.player_name, c.season, COALESCE(a.active, 0) AS active
  FROM calendar c
  LEFT JOIN activity a USING (player_name, season)
),
lagged AS (
  SELECT *, LAG(active) OVER (PARTITION BY player_name ORDER BY season) AS prev_active
  FROM timeline
)
SELECT
  player_name,
  season,
  CASE
    WHEN prev_active IS NULL AND active = 1 THEN 'New'
    WHEN prev_active = 1 AND active = 0 THEN 'Retired'
    WHEN prev_active = 1 AND active = 1 THEN 'Continued Playing'
    WHEN prev_active = 0 AND active = 1 THEN 'Returned from Retirement'
    WHEN prev_active = 0 AND active = 0 THEN 'Stayed Retired'
  END AS player_status
FROM lagged
ORDER BY player_name, season;