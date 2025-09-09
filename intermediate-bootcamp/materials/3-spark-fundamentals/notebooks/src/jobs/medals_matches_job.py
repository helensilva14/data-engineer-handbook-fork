from pyspark.sql import SparkSession

query = ""

def do_medals_matches_transformation(spark, dataframe):
    dataframe.createOrReplaceTempView("medals_matches")
    return spark.sql(query)


def main():
    spark = SparkSession.builder \
      .master("local") \
      .appName("medals_matches") \
      .getOrCreate()
    output_df = do_medals_matches_transformation(spark, spark.table("medals_matches"))
    output_df.write.mode("overwrite").insertInto("medals_matches")