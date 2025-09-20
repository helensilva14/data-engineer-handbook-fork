import os

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def create_processed_events_source_kafka(t_env):
    kafka_key = os.environ.get("KAFKA_WEB_TRAFFIC_KEY", "")
    kafka_secret = os.environ.get("KAFKA_WEB_TRAFFIC_SECRET", "")
    table_name = "process_events_kafka"
    pattern = "yyyy-MM-dd''T''HH:mm:ss.SSS''Z''"
    source_ddl = f"""
        CREATE TABLE {table_name} (
            ip VARCHAR,
            event_time TIMESTAMP_LTZ(3),
            referrer VARCHAR,
            host VARCHAR,
            url VARCHAR,
            geodata VARCHAR,
            WATERMARK FOR event_time AS event_time - INTERVAL '15' SECOND
        ) WITH (
            'connector' = 'kafka',
            'properties.bootstrap.servers' = '{os.environ.get('KAFKA_URL')}',
            'topic' = '{os.environ.get('KAFKA_TOPIC')}',
            'properties.group.id' = '{os.environ.get('KAFKA_GROUP')}',
            'properties.security.protocol' = 'SASL_SSL',
            'properties.sasl.mechanism' = 'PLAIN',
            'properties.sasl.jaas.config' = 'org.apache.flink.kafka.shaded.org.apache.kafka.common.security.plain.PlainLoginModule required username=\"{kafka_key}\" password=\"{kafka_secret}\";',
            'scan.startup.mode' = 'latest-offset',
            'properties.auto.offset.reset' = 'latest',
            'format' = 'json',
            'json.timestamp-format.standard' = 'ISO-8601'
        );
    """
    t_env.execute_sql(source_ddl)
    return table_name


def create_sessionized_events_sink_postgres(t_env):
    table_name = "sessionized_events"
    sink_ddl = f"""
        CREATE TABLE {table_name} (
            session_id STRING,
            session_start TIMESTAMP(3),
            session_end TIMESTAMP(3),
            ip VARCHAR,
            host VARCHAR,
            event_count BIGINT,
            PRIMARY KEY (session_id) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = '{os.environ.get("POSTGRES_URL")}',
            'table-name' = '{table_name}',
            'username' = '{os.environ.get("POSTGRES_USER", "postgres")}',
            'password' = '{os.environ.get("POSTGRES_PASSWORD", "postgres")}',
            'driver' = 'org.postgresql.Driver'
        );
    """
    t_env.execute_sql(sink_ddl)
    return table_name


def log_sessionization():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10_000) # every 10 seconds 
    env.set_parallelism(3)

    # Set up the table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    try:
        # Create Kafka table
        source_table = create_processed_events_source_kafka(t_env)
        # Create the sink table
        sink_table = create_sessionized_events_sink_postgres(t_env)

        # Apply a session window grouped by IP and host        
        session_sql = f"""
            SELECT
                MD5(CONCAT_WS('-', 
                    COALESCE(ip,''), 
                    COALESCE(host,''), 
                    CAST(SESSION_START(event_time, INTERVAL '5' MINUTE) AS STRING), 
                    CAST(SESSION_END(event_time, INTERVAL '5' MINUTE) AS STRING))
                ) AS session_id,
                SESSION_START(event_time, INTERVAL '5' MINUTE) AS session_start,
                SESSION_END(event_time, INTERVAL '5' MINUTE) AS session_end,
                ip,
                host,
                COUNT(*) AS event_count
            FROM {source_table}
            GROUP BY
                SESSION(event_time, INTERVAL '5' MINUTE),
                ip,
                host
        """
        
        # Execute the SQL query
        session_table = t_env.sql_query(session_sql)

        # Insert the results into the sink table
        session_table.execute_insert(sink_table).wait()

    except Exception as e:
        print("Writing records from Kafka to Postgres failed:", str(e))


if __name__ == '__main__':
    log_sessionization()
