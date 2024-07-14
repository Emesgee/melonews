from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the path to the scraper script
sys.path.append(str(Path(__file__).resolve().parents[1] / 'scripts'))
# Import your Kafka consumer script function
from scraper_consumer import kafka_consumer_process  # Adjusted import

# Default arguments for the DAG
default_args = {    
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),  # Adjust the start date as necessary
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
# Add the path to the scraper script
sys.path.append(str(Path(__file__).resolve().parents[1] / 'scripts'))
# Define the DAG
dag = DAG(
    'kafka_consumer_dag',
    default_args=default_args,
    description='A DAG to consume messages from Kafka and store in PostgreSQL and local JSON',
    schedule_interval=timedelta(minutes=5),  # Adjust the interval as needed
)

# Define the PythonOperator to run the Kafka consumer process
kafka_consumer_task = PythonOperator(
    task_id='run_kafka_consumer',
    python_callable=kafka_consumer_process,
    dag=dag,
)

# This DAG has only one task
kafka_consumer_task
