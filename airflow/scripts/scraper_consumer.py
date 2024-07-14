from confluent_kafka import Consumer, KafkaError
import json
import psycopg2

def kafka_consumer_process():
    # Kafka consumer configuration
    kafka_conf = {
        'bootstrap.servers': 'localhost:9092',  # Update with your Kafka broker(s)
        'group.id': 'my_consumer_group',        # Consumer group ID
        'auto.offset.reset': 'earliest'         # Start reading from the beginning of the topic
    }

    # PostgreSQL connection configuration
    pg_conf = {
        'dbname': 'your_database_name',    # Update with your PostgreSQL database name
        'user': 'your_username',           # Update with your PostgreSQL username
        'password': 'your_password',       # Update with your PostgreSQL password
        'host': 'localhost',               # Update with your PostgreSQL host
        'port': 5432                       # Update with your PostgreSQL port (default is 5432)
    }

    # Local JSON file path
    local_json_file_path = '/opt/airflow/dags/data/output.json'  # Update with your desired file path

    # Create Kafka consumer
    consumer = Consumer(kafka_conf)

    # Subscribe to Kafka topic
    topic = 'eyesonpalestine'  # Update with your Kafka topic name
    consumer.subscribe([topic])

    # SQL query to insert JSON data
    insert_query = """
    INSERT INTO kafka_json_data (json_data) VALUES (%s);
    """  # Update 'kafka_json_data' with your actual table name and 'json_data' with your column name

    conn = None
    cur = None

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**pg_conf)
        cur = conn.cursor()

        # Open local JSON file for writing
        with open(local_json_file_path, 'a') as local_json_file:
            
            timeout_counter = 0  # Initialize timeout counter
            timeout_limit = 10    # Number of consecutive empty polls before exiting

            while True:
                # Poll for new messages from Kafka
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    timeout_counter += 1
                    if timeout_counter >= timeout_limit:
                        print("No new messages received. Exiting...")
                        break
                    continue
                timeout_counter = 0  # Reset timeout counter if a message is received
                
                if msg.error():
                    # Handle errors
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition
                        print(f"Reached end of partition {msg.partition()}")
                    else:
                        # Other errors
                        print(f"Error: {msg.error()}")
                    continue

                # Decode message value (assumed to be in JSON format)
                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
                    continue

                # Insert JSON data into PostgreSQL
                try:
                    cur.execute(insert_query, [json.dumps(message_data)])
                    conn.commit()
                    print(f"Message written to PostgreSQL: {message_data}")
                except psycopg2.Error as e:
                    print(f"Failed to insert data into PostgreSQL: {e}")
                    conn.rollback()

                # Write JSON data to local file
                json.dump(message_data, local_json_file)
                local_json_file.write('\n')

    except KeyboardInterrupt:
        pass

    finally:
        # Close Kafka consumer and PostgreSQL connection
        consumer.close()
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    kafka_consumer_process()
