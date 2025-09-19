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
SELECT host, AVG(event_count) AS avg_events_per_session
FROM public.sessionized_events
WHERE host LIKE '%techcreator%'
GROUP BY host;

-- Compare results between different hosts (zachwilson.techcreator.io, zachwilson.tech, lulu.techcreator.io)
SELECT host, AVG(event_count) AS avg_events_per_session
FROM public.sessionized_events
WHERE host IN ('zachwilson.techcreator.io','zachwilson.tech','lulu.techcreator.io')
GROUP BY host;