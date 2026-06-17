FROM apache/airflow:2.8.0

USER airflow

RUN pip install --no-cache-dir \
    apache-airflow-providers-google==10.13.0 \
    pyiceberg[gcs]==0.7.1 \
    pandas==2.0.3 \
    pyarrow==12.0.1 \
    psycopg2-binary==2.9.9