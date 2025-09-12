from chispa.dataframe_comparer import *
from collections import namedtuple

from ..jobs.actors_scd_job import do_actors_scd_transformation

Actor = namedtuple("Actor", "actor_id actor_name quality_class is_active current_year quality_class_changed is_active_changed")
ActorScd = namedtuple("ActorScd", "actor_id actor_name quality_class is_active start_date end_date")

def test_scd_generation(spark):
    source_data = [
        Actor(1, "Some Actress", "Good", True, 2001, False, False),
        Actor(1, "Some Actress", "Great", True, 2002, True, False),
        Actor(1, "Some Actress", "Great", False, 2003, False, True),
    ]
    source_df = spark.createDataFrame(source_data)

    actual_df = do_actors_scd_transformation(spark, source_df)

    expected_data = [
        ActorScd(1, "Some Actress", "Good", True, 2001, 2001),
        ActorScd(1, "Some Actress", "Great", True, 2002, 2002),
        ActorScd(1, "Some Actress", "Great", False, 2003, 2003),
    ]
    expected_df = spark.createDataFrame(expected_data)
    
    assert_df_equality(actual_df, expected_df)