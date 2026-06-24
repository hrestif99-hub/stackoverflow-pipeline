from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

default_args = {
    'owner': 'hugues',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='stackoverflow_pipeline',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 0 * * *',
    catchup=False,
    description='Pipeline quotidien Stack Overflow',
) as dag:

    def appeler_cloud_function():
        url = "https://europe-west1-stackoverflow-pipeline.cloudfunctions.net/stackoverflow-ingestion"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Cloud Function a échoué : {response.status_code}")
        print(f"Cloud Function appelée avec succès : {response.text}")

    def lire_pubsub():
        from google.cloud import pubsub_v1
        project_id = "stackoverflow-pipeline"
        subscription_id = "stackoverflow-questions-sub"
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)
        messages = []
        while True:
            response = subscriber.pull(
                request={"subscription": subscription_path, "max_messages": 1000}
            )
            if not response.received_messages:
                break
            ack_ids = []
            for msg in response.received_messages:
                data = msg.message.data.decode("utf-8")
                messages.append(data)
                ack_ids.append(msg.ack_id)
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
        print(f"{len(messages)} messages récupérés depuis Pub/Sub")
        return messages

    def inserer_dans_postgres(**context):
        import json
        import psycopg2
        from datetime import datetime
        messages = context['ti'].xcom_pull(task_ids='lire_pubsub')
        if not messages:
            print("Aucun message à insérer")
            return
        conn = psycopg2.connect(
            host="stackoverflow_postgres",
            database="stackoverflow",
            user="airflow",
            password="airflow"
        )
        cursor = conn.cursor()
        inseres = 0
        ignores = 0
        for message in messages:
            question = json.loads(message)
            try:
                cursor.execute("""
                    INSERT INTO questions
                        (id, title, creation_date, tags, score, answer_count)
                    VALUES
                        (%(question_id)s, %(title)s, %(creation_date)s,
                         %(tags)s, %(score)s, %(answer_count)s)
                    ON CONFLICT (id) DO NOTHING
                """, {
                    **question,
                    'creation_date': datetime.utcfromtimestamp(question['creation_date'])
                })
                inseres += 1
            except Exception as e:
                print(f"Question ignorée : {e}")
                ignores += 1
        conn.commit()
        cursor.close()
        conn.close()
        print(f"{inseres} questions insérées, {ignores} ignorées")

    def exporter_vers_gcs(**context):
        import pandas as pd              # pour manipuler les données comme un tableau
        import pyarrow.parquet as pq     # pour créer des fichiers Parquet
        import psycopg2                  # pour se connecter à PostgreSQL
        from google.cloud import storage # pour envoyer des fichiers dans GCS
        from datetime import date        # pour récupérer la date d'aujourd'hui
        import io                        # pour créer un fichier en mémoire (sans toucher le disque)

        # On se connecte à PostgreSQL
        conn = psycopg2.connect(
            host="stackoverflow_postgres", # nom du container PostgreSQL dans Docker
            database="stackoverflow",      # nom de la base de données
            user="airflow",                # utilisateur
            password="airflow"             # mot de passe
        )

        # On lit UNIQUEMENT les questions créées aujourd'hui
        jour_des_donnees = date.today().isoformat()                # ex: "2026-06-17" → nom du fichier
        premier_du_mois = date.today().replace(day=1).isoformat()  # ex: "2026-06-01" → nom du dossier
        df = pd.read_sql("""
            SELECT id, title, creation_date, tags, score, answer_count
            FROM questions
            WHERE DATE(creation_date) = CURRENT_DATE
        """, conn)
        conn.close() # on ferme la connexion PostgreSQL, on en a plus besoin

        # Si aucune question aujourd'hui, on arrête là
        if df.empty:
            print("Aucune question aujourd'hui, rien à exporter")
            return

        print(f"{len(df)} questions à exporter vers GCS")

        # On convertit le tableau en fichier Parquet dans la mémoire RAM
        # (pas besoin d'écrire sur le disque, plus rapide et plus propre)
        buffer = io.BytesIO()            # on crée un "fichier virtuel" en mémoire
        df.to_parquet(buffer, index=False) # on écrit le Parquet dedans
        buffer.seek(0)                   # on remet le curseur au début du fichier

        # On se connecte à GCS et on envoie le fichier
        client = storage.Client()        # connexion à GCS (utilise automatiquement gcp-credentials.json)
        bucket = client.bucket("stackoverflow-pipeline-lake") # on cible notre bucket
        blob_path = f"stackoverflow/questions/date={premier_du_mois}/questions_{jour_des_donnees}.parquet"
        blob = bucket.blob(blob_path)    # on prépare l'objet fichier
        blob.upload_from_file(buffer, content_type="application/octet-stream") # on envoie !

        print(f"Fichier envoyé : gs://stackoverflow-pipeline-lake/{blob_path}")

    tache_1 = PythonOperator(
        task_id='appeler_cloud_function',
        python_callable=appeler_cloud_function,
    )

    tache_2 = PythonOperator(
        task_id='lire_pubsub',
        python_callable=lire_pubsub,
    )

    tache_3 = PythonOperator(
        task_id='inserer_dans_postgres',
        python_callable=inserer_dans_postgres,
        provide_context=True,
    )

    tache_4 = PythonOperator(
        task_id='exporter_vers_gcs',       # nom affiché dans l'interface Airflow
        python_callable=exporter_vers_gcs, # la fonction à exécuter
        provide_context=True,              # donne accès aux infos du DAG (date, etc.)
    )

    tache_1 >> tache_2 >> tache_3 >> tache_4 # ordre d'exécution des tâches