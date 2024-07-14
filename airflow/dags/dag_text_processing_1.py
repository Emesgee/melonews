# text_processing_dag_1.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import sys
import os

# Add the path to the scripts directory (adjust based on your setup)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from text_processing import process_text  # Importing the process_text function

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 6, 18),
    'retries': 1,
}

dag_id = 'text_processing_dag_1'
input_path = '/opt/airflow/data/output_data.json'
output_path = '/opt/airflow/data/processed_data_1.json'

dag = DAG(
    dag_id,
    default_args=default_args,
    description='A simple text processing DAG',
    schedule_interval='@once',
    catchup=False
)

with dag:
    process_text_task = PythonOperator(
        task_id='process_text',
        python_callable=process_text,
        op_kwargs={'input_path': input_path, 'output_path': output_path},
        dag=dag,
    )

    # Optionally, you can define dependencies between tasks if needed
    # For example, process_text_task.set_upstream(some_other_task)
