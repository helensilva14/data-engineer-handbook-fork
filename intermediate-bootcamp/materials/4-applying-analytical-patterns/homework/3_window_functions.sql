WITH game_details_augmented AS (
    SELECT
        gd.game_id AS game_id,
        gd.team_abbreviation AS team,
        g.game_date_est AS game_date,
        g.season AS season,
        gd.player_name AS player_name,
        COALESCE(gd.pts, 0) AS pts, 
        CASE
            WHEN g.home_team_id = gd.team_id AND g.home_team_wins = 1
                THEN 1
            ELSE 0
        END AS team_won
    FROM game_details gd
    JOIN games g ON gd.game_id = g.game_id
    WHERE gd.start_position IS NOT NULL
)
SELECT 
    game_id,
    season,
    team,
    game_date,
    player_name,
    pts,
    SUM(team_won) OVER (
        PARTITION BY game_id, team
        ORDER BY game_date
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) AS wins_last_90_games
FROM game_details_augmented