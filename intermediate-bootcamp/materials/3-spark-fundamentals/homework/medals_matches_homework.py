#!/usr/bin/env python
# coding: utf-8

# To force a PySpark notebook to create a new Spark session with custom configurations, rather than using an existing or default one, follow these steps:
# 
# - **Stop any existing Spark Session:** If a Spark session is already active in your notebook environment (e.g., from a previous run or automatic startup), you must stop it before creating a new one. This ensures that the new session is truly independent and applies your custom configurations from scratch.

# In[1]:


if 'spark' in locals() and spark is not None:
    spark.stop()


# In[15]:


from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast, avg, desc, col

spark = SparkSession.builder \
      .appName("medals_matches_homework") \
      .config("spark.sql.autoBroadcastJoinThreshold", "-1") \
      .getOrCreate()

spark


# In[3]:


SHARED_PATH = "/home/iceberg/notebooks/notebooks/data"

match_details = spark.read.option("header","true").option("inferSchema", "true").csv(f"{SHARED_PATH}/match_details.csv")
matches = spark.read.option("header","true").option("inferSchema", "true").csv(f"{SHARED_PATH}/matches.csv")
medals_matches_players = spark.read.option("header","true").option("inferSchema", "true").csv(f"{SHARED_PATH}/medals_matches_players.csv")
medals = spark.read.option("header","true").option("inferSchema", "true").csv(f"{SHARED_PATH}/medals.csv")
maps = spark.read.option("header","true").option("inferSchema", "true").csv(f"{SHARED_PATH}/maps.csv")

print(f"{match_details.count()}, {matches.count()}, {medals_matches_players.count()}, {medals.count()}, {maps.count()}")


# In[4]:


medals_joined = medals_matches_players.join(broadcast(medals), "medal_id")

medals_joined.head()


# In[5]:


matches_joined = matches.join(broadcast(maps), "mapid")

matches_joined.head()


# In[6]:


spark.sql("DROP TABLE IF EXISTS bootcamp.bucketed_match_details")
ddl_match_details = """
CREATE TABLE IF NOT EXISTS bootcamp.bucketed_match_details (
     match_id STRING,
     player_gamertag STRING,
     player_total_kills INTEGER,
     player_total_deaths INTEGER
)
USING iceberg
PARTITIONED BY (bucket(16, match_id));
"""
spark.sql(ddl_match_details)

spark.sql("DROP TABLE IF EXISTS bootcamp.bucketed_matches")
ddl_matches = """
CREATE TABLE IF NOT EXISTS bootcamp.bucketed_matches (
     match_id STRING,
     mapid STRING,
     is_team_game BOOLEAN,
     playlist_id STRING,
     completion_date TIMESTAMP
 )
USING iceberg
PARTITIONED BY (completion_date, bucket(16, match_id));
"""
spark.sql(ddl_matches)

spark.sql("DROP TABLE IF EXISTS bootcamp.bucketed_medal_matches_players")
ddl_match_details = """
CREATE TABLE IF NOT EXISTS bootcamp.bucketed_medal_matches_players (
     match_id STRING,
     player_gamertag STRING,
     medal_id STRING,
     count INTEGER
)
USING iceberg
PARTITIONED BY (bucket(16, match_id));
"""
spark.sql(ddl_match_details)


# In[7]:


# Saving DataFrames as bucketed tables
match_details.select("match_id", "player_gamertag", "player_total_kills", "player_total_deaths") \
    .write.mode("overwrite") \
    .bucketBy(16, "match_id") \
    .saveAsTable("bootcamp.bucketed_match_details")

matches.select("match_id", "mapid", "is_team_game", "playlist_id", "completion_date") \
    .write.mode("overwrite") \
    .partitionBy("completion_date") \
    .bucketBy(16, "match_id") \
    .saveAsTable("bootcamp.bucketed_matches")

medals_matches_players.write.mode("overwrite") \
    .bucketBy(16, "match_id") \
    .saveAsTable("bootcamp.bucketed_medal_matches_players")

# Reading the bucketed tables
bucketed_match_details = spark.table("bootcamp.bucketed_match_details")
bucketed_matches = spark.table("bootcamp.bucketed_matches")
bucketed_medal_matches_players = spark.table("bootcamp.bucketed_medal_matches_players")


# In[20]:


# The join will automatically use the bucketing since all tables are bucketed
joined_df = bucketed_match_details.alias("md") \
    .join(bucketed_matches.alias("m"), "match_id") \
    .join(bucketed_medal_matches_players.alias("mmp"), "match_id") \
    .select(
        "match_id",
        "md.player_gamertag",  # Explicitly getting value from match_details (duplicate column)
        "player_total_kills",
        "player_total_deaths",
        "mapid",
        "is_team_game",
        "playlist_id",
        "medal_id",
        "count",
        "completion_date"
    )

joined_df.head()


# In[21]:


# Question 1 - Which player averages the most kills per game?
player_avg_kills = joined_df.groupBy("player_gamertag") \
    .agg(avg("player_total_kills").alias("avg_kills_per_game")) \
    .orderBy(desc("avg_kills_per_game"))

player_avg_kills.head(3)


# In[10]:


# Question 2 - Which playlist gets played the most?
executed_playlists = joined_df.groupBy("playlist_id") \
    .count() \
    .withColumnRenamed("count", "execution_count") \
    .orderBy(desc("execution_count"))

executed_playlists.head(3)


# In[11]:


# Question 3 - Which map gets played the most?
played_maps = joined_df.groupBy("mapid") \
    .count() \
    .withColumnRenamed("count", "played_count") \
    .orderBy(desc("played_count"))

played_maps.head(3)


# In[16]:


# Question 4 - Which map do players get the most Killing Spree medals on?
most_killing_spree_maps = joined_df \
    .join(medals, "medal_id") \
    .where(col("name") == "Killing Spree") \
    .groupBy("mapid") \
    .count() \
    .withColumnRenamed("count", "medal_count") \
    .orderBy(desc("medal_count"))

most_killing_spree_maps.head(3)


# #### With the aggregated dataset, testing different .sortWithinPartitions() to see which has the smallest data size (hint: playlists and maps are both very low cardinality)

# In[17]:


spark.sql("DROP TABLE IF EXISTS bootcamp.sorted_matches")
ddl_sorted_matches = """
CREATE TABLE IF NOT EXISTS bootcamp.sorted_matches (
     match_id STRING,
     player_gamertag STRING,
     player_total_kills INTEGER,
     player_total_deaths INTEGER,
     mapid STRING,
     is_team_game BOOLEAN,
     playlist_id STRING,
     medal_id STRING,
     count INTEGER,
     completion_date TIMESTAMP
 )
USING iceberg
PARTITIONED BY (year(completion_date));
"""
spark.sql(ddl_sorted_matches)


# In[22]:


joined_df \
    .sortWithinPartitions(col("completion_date"), col("mapid")) \
    .write.mode("overwrite") \
    .saveAsTable("bootcamp.sorted_matches")


# In[23]:


get_ipython().run_cell_magic('sql', '', '\nSELECT SUM(file_size_in_bytes) as file_size_in_bytes, COUNT(1) as num_files \nFROM demo.bootcamp.sorted_matches.files\n')


# In[24]:


joined_df \
    .sortWithinPartitions(col("completion_date"), col("playlist_id")) \
    .write.mode("overwrite") \
    .saveAsTable("bootcamp.sorted_matches")


# In[25]:


get_ipython().run_cell_magic('sql', '', '\nSELECT SUM(file_size_in_bytes) as file_size_in_bytes, COUNT(1) as num_files \nFROM demo.bootcamp.sorted_matches.files\n')


# In[26]:


joined_df \
    .sortWithinPartitions(col("completion_date"), col("playlist_id"), col("mapid")) \
    .write.mode("overwrite") \
    .saveAsTable("bootcamp.sorted_matches")


# In[27]:


get_ipython().run_cell_magic('sql', '', '\nSELECT SUM(file_size_in_bytes) as file_size_in_bytes, COUNT(1) as num_files \nFROM demo.bootcamp.sorted_matches.files\n')


# In[28]:


joined_df \
    .sortWithinPartitions(col("completion_date"), col("mapid"), col("playlist_id")) \
    .write.mode("overwrite") \
    .saveAsTable("bootcamp.sorted_matches")


# In[29]:


get_ipython().run_cell_magic('sql', '', '\nSELECT SUM(file_size_in_bytes) as file_size_in_bytes, COUNT(1) as num_files \nFROM demo.bootcamp.sorted_matches.files\n')

