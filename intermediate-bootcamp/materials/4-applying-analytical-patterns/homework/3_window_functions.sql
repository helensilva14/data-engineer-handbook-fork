CREATE TABLE game_details_rolling_dashboard AS
WITH game_details_augmented AS (
    SELECT
        gd.game_id AS game_id,
        gd.team_abbreviation AS team,
        g.game_date_est AS game_date,
        gd.player_name AS player_name,
        COALESCE(gd.pts, 0) AS pts, 
        CASE
            WHEN g.home_team_id = gd.team_id AND g.home_team_wins = 1
                THEN 1
            WHEN g.visitor_team_id = gd.team_id AND g.home_team_wins = 0
                THEN 1
            ELSE 0
        END AS team_won
    FROM game_details gd
    JOIN games g ON gd.game_id = g.game_id
)
SELECT 
    game_id,
    team,
    game_date,
    player_name,
    pts,
    SUM(team_won) OVER (
        PARTITION BY team
        ORDER BY game_date, game_id
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) AS wins_last_90_games
FROM game_details_augmented;

-- Question 1: What is the most games a team has won in a 90 game stretch?
SELECT team, MAX(wins_last_90_games) AS max_wins_last_90_games
FROM game_details_rolling_dashboard
GROUP BY team
ORDER BY max_wins_last_90_games DESC
LIMIT 1;

-- Question 2: How many games in a row did LeBron James score over 10 points a game?
WITH lebron_games AS (
    SELECT 
        game_id,
        game_date,
        CASE WHEN pts > 10 THEN 1 ELSE 0 END AS pts_over_10
    FROM game_details_rolling_dashboard
    WHERE player_name = 'LeBron James'
),
streak_breaks AS (
    SELECT 
        game_id,
        game_date,
        SUM(CASE WHEN pts_over_10 = 0 THEN 1 ELSE 0 END) OVER (
            ORDER BY game_date, game_id
        ) AS games_below_10_pts
    FROM lebron_games
)
SELECT 
    COUNT(CASE WHEN games_below_10_pts = 0 THEN 1 END) AS max_streak_over_10_pts
FROM streak_breaks;