from airflow import DAG
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 6, 18),
    'retries': 1,
}

dag = DAG(
    'orchestrator_dag',
    default_args=default_args,
    description='An orchestrator DAG to chain text processing DAGs',
    schedule_interval='@once',
    catchup=False
)

start = DummyOperator(
    task_id='start',
    dag=dag,
)

trigger_dag_1 = TriggerDagRunOperator(
    task_id='trigger_text_processing_dag_1',
    trigger_dag_id='text_processing_dag_1',
    dag=dag,
)

trigger_dag_2 = TriggerDagRunOperator(
    task_id='trigger_text_processing_dag_2',
    trigger_dag_id='text_processing_dag_2',
    dag=dag,
)

end = DummyOperator(
    task_id='end',
    dag=dag,
)

start >> trigger_dag_1 >> trigger_dag_2 >> end
