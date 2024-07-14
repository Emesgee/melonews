# Start from the Apache Airflow 2.2.4 base image
FROM apache/airflow:2.2.4

# Switch to root user to install dependencies
USER root

# Install necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        wget \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        libffi-dev \
        liblzma-dev \
        python3-dev \
        nano \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools globally
RUN pip install --upgrade pip setuptools

# Add airflow user to sudoers with root privileges
RUN echo "airflow ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch back to airflow user
USER airflow

# Set working directory
WORKDIR /opt/airflow

# Copy requirements.txt and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
RUN python -m spacy download en

# Expose necessary ports
EXPOSE 8080

# Initialize Airflow database
RUN airflow db init

# Create Airflow admin user
RUN airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Define the command to start Airflow services
CMD ["bash", "-c", "airflow webserver --port 8080 & airflow scheduler"]
