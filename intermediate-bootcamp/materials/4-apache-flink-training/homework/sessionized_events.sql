CREATE TABLE public.sessionized_events (
    session_id VARCHAR,
    session_start TIMESTAMP(3),
    session_end TIMESTAMP(3),
    ip VARCHAR,
    host VARCHAR,
    event_count BIGINT,
    PRIMARY KEY (session_id)
);

-- What is the average number of web events of a session from a user on Tech Creator?
SELECT ROUND(AVG(event_count), 2) AS avg_events_per_session
FROM public.sessionized_events
WHERE host LIKE '%techcreator%';
-- Output: 2.17

-- Compare results between different hosts (zachwilson.techcreator.io, zachwilson.tech, lulu.techcreator.io)
SELECT host, ROUND(AVG(event_count), 2) AS avg_events_per_session
FROM public.sessionized_events
WHERE host IN ('zachwilson.techcreator.io','zachwilson.tech','lulu.techcreator.io')
GROUP BY host
ORDER BY host;
-- Output:
-- host | avg_events_per_session
-- zachwilson.techcreator.io | 0.51