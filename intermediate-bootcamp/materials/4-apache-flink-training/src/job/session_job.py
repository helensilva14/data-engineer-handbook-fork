import os

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment
from pyflink.table.expressions import lit, col
from pyflink.table.window import Session


def create_processed_events_source_kafka(t_env):
    kafka_key = os.environ.get("KAFKA_WEB_TRAFFIC_KEY", "")
    kafka_secret = os.environ.get("KAFKA_WEB_TRAFFIC_SECRET", "")
    table_name = "process_events_kafka"
    pattern = "yyyy-MM-dd''T''HH:mm:ss.SSS''Z''"
    source_ddl = f"""
        CREATE TABLE {table_name} (
            ip VARCHAR,
            event_time VARCHAR,
            referrer VARCHAR,
            host VARCHAR,
            url VARCHAR,
            geodata VARCHAR,
            window_timestamp AS TO_TIMESTAMP(event_time, '{pattern}'),
            WATERMARK FOR window_timestamp AS window_timestamp - INTERVAL '15' SECOND
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
            'format' = 'json'
        );
    """
    t_env.execute_sql(source_ddl)
    return table_name


def create_result_sink_print(t_env):
    table_name = "session_results_print"
    sink_ddl = f"""
        CREATE TABLE {table_name} (
            session_start TIMESTAMP(3),
            session_end TIMESTAMP(3),
            ip VARCHAR,
            host VARCHAR,
            event_count BIGINT
        ) WITH (
            'connector' = 'print'
        );
    """
    t_env.execute_sql(sink_ddl)
    return table_name


def log_sessionization():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10)
    env.set_parallelism(3)

    # Set up the table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    try:
        # Create Kafka table
        source_table = create_processed_events_source_kafka(t_env)
        # Create the sink table
        sink_table = create_result_sink_print(t_env)

        # Apply a session window to the data, grouped by IP and host
        session_table = t_env \
            .from_path(source_table) \
            .window(
                Session.with_gap(lit(5).minutes).on(col("window_timestamp")).alias("w")
            ).group_by(
                col("w"),
                col("ip"),
                col("host")
            ) \
            .select(
                # Get the session start, end and the count of events in the session
                col("w").start.alias("session_start"),
                col("w").end.alias("session_end"),
                col("ip"),
                col("host"),
                col("ip").count.alias("event_count")
            )
        
        # Insert the results into the sink table
        # This will trigger the streaming job execution
        session_table.execute_insert(sink_table)

    except Exception as e:
        print("Writing records from Kafka to sink failed:", str(e))


if __name__ == '__main__':
    log_sessionization()
