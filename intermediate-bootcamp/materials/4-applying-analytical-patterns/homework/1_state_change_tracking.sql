WITH yesterday AS (
    SELECT * FROM players
    WHERE current_season = 1998
),
today AS (
    SELECT * FROM players
    WHERE current_season = 1999
)
SELECT 
    COALESCE(t.player_name, y.player_name) AS player_name,
    CASE
        WHEN y.player_name IS NULL 
            THEN 'New'
        WHEN y.is_active IS TRUE AND t.player_name IS NULL
            THEN 'Retired'
        WHEN y.is_active IS TRUE AND t.player_name IS NOT NULL
            THEN 'Continued Playing'
        WHEN y.is_active IS FALSE AND t.player_name IS NOT NULL 
            THEN 'Returned from Retirement'
        ELSE 'Stayed Retired'
    END 
        AS player_status,
    COALESCE(t.current_season, y.current_season) as current_season
FROM today t
FULL OUTER JOIN yesterday y
ON t.player_name = y.player_name;
