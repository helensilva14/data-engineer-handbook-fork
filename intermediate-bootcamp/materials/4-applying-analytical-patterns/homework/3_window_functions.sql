-- Question 1: What is the most games a team has won in a 90 game stretch?
WITH team_games AS (
  SELECT
    gd.team_abbreviation AS team,
    g.game_id,
    g.game_date_est AS game_date,
    MAX(CASE
      WHEN g.home_team_id = gd.team_id AND g.home_team_wins = 1 THEN 1
      WHEN g.visitor_team_id = gd.team_id AND g.home_team_wins = 0 THEN 1
      ELSE 0
    END) AS team_won
  FROM game_details gd
  JOIN games g USING (game_id)
  GROUP BY gd.team_abbreviation, g.game_id, g.game_date_est
),
ordered_games AS (
  SELECT *,
        ROW_NUMBER() OVER (PARTITION BY team ORDER BY game_date, game_id) AS row_num
  FROM team_games
),
rolling_window AS (
  SELECT 
        team, row_num,
        SUM(team_won) OVER 
            (PARTITION BY team ORDER BY row_num ROWS BETWEEN 89 PRECEDING AND CURRENT ROW)
            AS wins_last_90_games
  FROM ordered_games
)
SELECT team, MAX(wins_last_90_games) AS max_wins_last_90_games
FROM rolling_window
GROUP BY team
ORDER BY max_wins_last_90_games DESC
LIMIT 1;

-- Question 2: How many games in a row did LeBron James score over 10 points a game?
WITH lebron_game_points AS (
  SELECT
    g.game_id,
    g.game_date_est AS game_date,
    COALESCE(SUM(gd.pts), 0) AS points_scored -- SUM to handle duplicates
  FROM game_details gd
  JOIN games g USING (game_id)
  WHERE gd.player_name = 'LeBron James'
  GROUP BY g.game_id, g.game_date_est
),
consecutive_scoring AS (
  SELECT *,
    CASE WHEN points_scored > 10 THEN 1 ELSE 0 END AS exceeded_10_pts
  FROM lebron_game_points
),
streak_groups AS (
  SELECT *,
    SUM(CASE WHEN exceeded_10_pts = 0 THEN 1 ELSE 0 END) OVER (ORDER BY game_date, game_id) AS group_id
  FROM consecutive_scoring
),
final_streaks AS (
  SELECT
    group_id,
    COUNT(*) AS streak_length
  FROM streak_groups
  WHERE exceeded_10_pts = 1
  GROUP BY group_id
)
SELECT MAX(streak_length) AS max_streak_over_10_pts
FROM final_streaks;