WITH game_details_augmented AS (
    SELECT
        gd.game_id AS game_id,
        gd.team_abbreviation AS team,
        g.season AS season,
        gd.player_name AS player_name, 
        COALESCE(gd.pts, 0) AS pts,
        CASE
            WHEN g.home_team_id = gd.team_id AND g.home_team_wins = 1
                THEN True
            ELSE False
        END AS team_won
    FROM game_details gd
    JOIN games g ON gd.game_id = g.game_id
    WHERE gd.start_position IS NOT NULL
)
SELECT
    CASE
        WHEN GROUPING(player_name) = 0
            AND GROUPING(team) = 0
                THEN 'player_name__team'
        WHEN GROUPING(player_name) = 0
            AND GROUPING(season) = 0
                THEN 'player_name__season'
        WHEN GROUPING(team) = 0 THEN 'team'
    END AS aggregation_level,
    COALESCE(player_name, '(overall)') as player_name,
    COALESCE(team, '(overall)') as team,
    COALESCE(CAST(season AS TEXT), '(overall)') as season,
    SUM(pts) as total_points,
    SUM(CASE WHEN team_won IS TRUE THEN 1 ELSE 0 END) as total_wins,
    COUNT(*) as total_games
FROM game_details_augmented
GROUP BY GROUPING SETS (
    (player_name, team),
    (player_name, season),
    (team)
)