CREATE TABLE game_details_dashboard AS
WITH game_details_augmented AS (
    SELECT
        gd.game_id AS game_id,
        gd.team_abbreviation AS team,
        g.season AS season,
        gd.player_name AS player_name, 
        COALESCE(gd.pts, 0) AS pts,
        CASE
            WHEN g.home_team_id = gd.team_id AND g.home_team_wins = 1
                THEN TRUE
            WHEN g.visitor_team_id = gd.team_id AND g.home_team_wins = 0
                THEN FALSE
            ELSE FALSE
        END AS team_won
    FROM game_details gd
    JOIN games g ON gd.game_id = g.game_id
)
SELECT
    CASE
        WHEN GROUPING(player_name) = 0 AND GROUPING(team) = 0
            THEN 'player_name__team'
        WHEN GROUPING(player_name) = 0 AND GROUPING(season) = 0
            THEN 'player_name__season'
        WHEN GROUPING(team) = 0 THEN 'team'
    END AS aggregation_level,
    COALESCE(player_name, '(overall)') AS player_name,
    COALESCE(team, '(overall)') AS team,
    COALESCE(CAST(season AS TEXT), '(overall)') AS season,
    SUM(pts) AS total_points,
    COUNT(DISTINCT game_id) FILTER (WHERE team_won IS TRUE) AS total_wins,
    COUNT(DISTINCT game_id) AS total_games
FROM game_details_augmented
GROUP BY GROUPING SETS (
    (player_name, team),
    (player_name, season),
    (team)
);

-- Question 1: Who scored the most points playing for one team?
SELECT *
FROM game_details_dashboard
WHERE aggregation_level = 'player_name__team'
ORDER BY total_points DESC
LIMIT 1;

-- Question 2: Who scored the most points in one season?
SELECT *
FROM game_details_dashboard
WHERE aggregation_level = 'player_name__season'
ORDER BY total_points DESC
LIMIT 1;

-- Question 3: Which team has won the most games?
SELECT *
FROM game_details_dashboard
WHERE aggregation_level = 'team'
ORDER BY total_wins DESC
LIMIT 1;