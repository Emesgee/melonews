from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the path to the scraper script
sys.path.append(str(Path(__file__).resolve().parents[1] / 'scripts'))

# Import the scrape_and_produce function
from scraper_producer import scrape_and_produce

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'webscraping_dag',
    default_args=default_args,
    description='A simple web scraping DAG',
    schedule_interval=timedelta(hours=1),  # Schedule the DAG to run every hour
)

# Define the PythonOperator to run the scraping function
scrape_task = PythonOperator(
    task_id='scrape_and_produce',
    python_callable=scrape_and_produce,
    dag=dag,
)

# This DAG has only one task
scrape_task
