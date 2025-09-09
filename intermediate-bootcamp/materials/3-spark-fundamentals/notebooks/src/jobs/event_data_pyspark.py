#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, col
spark = SparkSession.builder.appName("Jupyter").getOrCreate()

spark

events = spark.read.option("header", "true").csv("/home/iceberg/data/events.csv").withColumn("event_date", expr("DATE_TRUNC('day', event_time)"))
devices = spark.read.option("header","true").csv("/home/iceberg/data/devices.csv")

df = events.join(devices,on="device_id",how="left")
df = df.withColumnsRenamed({'browser_type': 'browser_family', 'os_type': 'os_family'})

df.show()


# In[5]:


sorted = df.repartition(10, col("event_date"))\
    .sortWithinPartitions(col("event_date"), col("host"))\
    .withColumn("event_time", col("event_time").cast("timestamp")) 

sortedTwo = df.repartition(10, col("event_date"))\
    .sort(col("event_date"), col("host"))\
    .withColumn("event_time", col("event_time").cast("timestamp")) 

sorted.show()
sortedTwo.show()


# In[ ]:


# .sortWithinPartitions() sorts within partitions, whereas .sort() is a global sort, which is very slow

# Note - exchange is synonymous with Shuffle


# In[6]:


sorted = df.repartition(10, col("event_date"))\
    .sortWithinPartitions(col("event_date"), col("host"))\
    .withColumn("event_time", col("event_time").cast("timestamp")) 

sortedTwo = df.repartition(10, col("event_date"))\
    .sort(col("event_date"), col("host"))\
    .withColumn("event_time", col("event_time").cast("timestamp")) 

sorted.explain()
sortedTwo.explain()


# In[7]:


get_ipython().run_cell_magic('sql', '', '\nCREATE DATABASE IF NOT EXISTS bootcamp\n')


# In[20]:


get_ipython().run_cell_magic('sql', '', '\nDROP TABLE IF EXISTS bootcamp.events\n')


# In[21]:


get_ipython().run_cell_magic('sql', '', '\nDROP TABLE IF EXISTS bootcamp.events_sorted\n')


# In[22]:


get_ipython().run_cell_magic('sql', '', '\nCREATE TABLE IF NOT EXISTS bootcamp.events (\n    url STRING,\n    referrer STRING,\n    browser_family STRING,\n    os_family STRING,\n    device_family STRING,\n    host STRING,\n    event_time TIMESTAMP,\n    event_date DATE\n)\nUSING iceberg\nPARTITIONED BY (years(event_date));\n')


# In[23]:


get_ipython().run_cell_magic('sql', '', '\n\nCREATE TABLE IF NOT EXISTS bootcamp.events_sorted (\n    url STRING,\n    referrer STRING,\n    browser_family STRING,\n    os_family STRING,\n    device_family STRING,\n    host STRING,\n    event_time TIMESTAMP,\n    event_date DATE\n)\nUSING iceberg\nPARTITIONED BY (years(event_date));\n')


# In[24]:


get_ipython().run_cell_magic('sql', '', '\n\nCREATE TABLE IF NOT EXISTS bootcamp.events_unsorted (\n    url STRING,\n    referrer STRING,\n    browser_family STRING,\n    os_family STRING,\n    device_family STRING,\n    host STRING,\n    event_time TIMESTAMP,\n    event_date DATE\n)\nUSING iceberg\nPARTITIONED BY (year(event_date));\n')


# In[26]:


start_df = df.repartition(4, col("event_date")).withColumn("event_time", col("event_time").cast("timestamp")) \
    
first_sort_df = start_df.sortWithinPartitions(col("event_date"), col("host"))

start_df.write.mode("overwrite").saveAsTable("bootcamp.events_unsorted")
first_sort_df.write.mode("overwrite").saveAsTable("bootcamp.events_sorted")


# In[121]:


get_ipython().run_cell_magic('sql', '', "\nSELECT SUM(file_size_in_bytes) as size, COUNT(1) as num_files, 'sorted' \nFROM demo.bootcamp.events_sorted.files\n\nUNION ALL\nSELECT SUM(file_size_in_bytes) as size, COUNT(1) as num_files, 'unsorted' \nFROM demo.bootcamp.events_unsorted.files\n\n\n\n")


# In[90]:


get_ipython().run_cell_magic('sql', '', 'SELECT SUM(file_size_in_bytes) as size, COUNT(1) as num_files FROM demo.bootcamp.events.files;\n')


# In[ ]:


get_ipython().run_cell_magic('sql', '', 'SELECT COUNT(1) FROM bootcamp.matches_bucketed.files\n')


# In[4]:





# In[ ]:




