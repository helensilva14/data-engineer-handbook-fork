from chispa.dataframe_comparer import *
from collections import namedtuple

from ..jobs.game_details_job import do_game_details_transformation

GameDetail = namedtuple("GameDetail", "game_id team_id team_abbreviation team_city player_id player_name pts")

def test_deduplication(spark):
    source_data = [
        GameDetail(1, 111, "GSW", "San Francisco", 22, "Player 22", "20"),
        GameDetail(1, 111, "GSW", "San Francisco", 22, "Player 22", "15"),
        GameDetail(1, 111, "GSW", "San Francisco", 22, "Player 22", "10"),
        GameDetail(2, 222, "ABC", "New York", 33, "Player 33", ""),
    ]
    source_df = spark.createDataFrame(source_data)

    actual_df = do_game_details_transformation(spark, source_df)

    expected_data = [
        GameDetail(1, 111, "GSW", "San Francisco", 22, "Player 22", "20"),
        GameDetail(2, 222, "ABC", "New York", 33, "Player 33", ""),
    ]
    expected_df = spark.createDataFrame(expected_data)
    
    assert_df_equality(actual_df, expected_df)