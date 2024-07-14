import pandas as pd
from sqlalchemy import create_engine

# Database connection parameters
db_params = {
    "username": "your_username",
    "password": "your_password",
    "host": "localhost",
    "port": "5432",
    "database": "your_database_name"
}

# Create the database connection URL
db_url = f"postgresql://{db_params['username']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"

# Create the SQLAlchemy engine
engine = create_engine(db_url)

# Define the SQL query
query = """
SELECT 
    (json_data->>'Time')::timestamp::date AS date,
    (json_data->>'Time')::timestamp::time AS time,
    (json_data->>'Message') as messages,
    (json_data->>'Video Links') as video_links,
    (json_data->>'Video Durations') as video_durations
FROM kafka_json_data;
"""

# Execute the query and fetch the results into a DataFrame
df = pd.read_sql(query, engine)

# Convert 'date' column to a standard date format (YYYY-MM-DD)
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

# Convert 'time' column to datetime with explicit format
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S', errors='coerce')

# Define the path to save the JSON file
json_file_path = "/home/mhmdghdbn/airflow/zookeeper/airflow/data/output_data.json"

# Save the DataFrame to a JSON file as a JSON array
df.to_json(json_file_path, orient='records', lines=False, force_ascii=False)
print(f"Results have been saved to {json_file_path}")
