WITH player_activity AS (
  SELECT player_name, season, 1 AS active
  FROM player_seasons
  GROUP BY player_name, season
),
timeline AS (
  SELECT
    player_name,
    season,
    COALESCE(active, 0) AS active,
    LAG(COALESCE(active, 0)) OVER (PARTITION BY player_name ORDER BY season) AS prev_active
  FROM player_activity
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
FROM timeline
ORDER BY season, player_name;