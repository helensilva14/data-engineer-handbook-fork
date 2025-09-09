from pyspark.sql import SparkSession

SHARED_PATH = "/home/iceberg/notebooks/notebooks/data"

query = ""

def read_csv_dataset(spark: SparkSession, dataset_name: str) -> "pyspark.sql.DataFrame":
    return spark.read.option("header", "true").csv(f"{SHARED_PATH}/{dataset_name}.csv")


def do_medals_matches_transformation(spark, dataframe):
    dataframe.createOrReplaceTempView("medals_matches")
    return spark.sql(query)


def main():
    spark = SparkSession.builder \
      .master("local") \
      .appName("medals_matches_homework") \
      .config("spark.sql.autoBroadcastJoinThreshold", "-1") \
      .getOrCreate()
    
    match_details = read_csv_dataset(spark, "match_details")
    matches = read_csv_dataset(spark, "matches")
    medals_matches_players = read_csv_dataset(spark, "medals_matches_players")
    medals = read_csv_dataset(spark, "medals")

    print(f"{match_details.count()}, {matches.count()}, {medals_matches_players.count()}, {medals.count()}")

    # output_df = do_medals_matches_transformation(spark, spark.table("medals_matches"))
    # output_df.write.mode("overwrite").insertInto("medals_matches")