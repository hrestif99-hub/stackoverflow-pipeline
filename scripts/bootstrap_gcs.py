import pandas as pd
import psycopg2
import os
from google.cloud import storage
import io
from dotenv import load_dotenv
load_dotenv()

# Connexion PostgreSQL
conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    database=os.environ.get("POSTGRES_DB", "stackoverflow"),
    user=os.environ.get("POSTGRES_USER", "airflow"),
    password=os.environ.get("POSTGRES_PASSWORD", "airflow"),
    port=os.environ.get("POSTGRES_PORT", "5432")
)

# On lit toutes les questions 2023-2026 par mois
print("Lecture des données PostgreSQL...")
df = pd.read_sql("""
    SELECT id, title, creation_date, tags, score, answer_count
    FROM questions
    WHERE creation_date >= '2022-09-01'
    AND creation_date < '2026-06-17'
""", conn)
conn.close()

print(f"{len(df)} questions récupérées")

# On groupe par mois et on envoie un fichier Parquet par mois
df['date'] = pd.to_datetime(df['creation_date']).dt.date
mois_list = pd.to_datetime(df['creation_date']).dt.to_period('M').unique()

client = storage.Client()
bucket = client.bucket("stackoverflow-pipeline-lake")

for mois in mois_list:
    df_mois = df[pd.to_datetime(df['creation_date']).dt.to_period('M') == mois]
    
    buffer = io.BytesIO()
    df_mois.to_parquet(buffer, index=False)
    buffer.seek(0)
    
    blob_path = f"stackoverflow/questions/date={mois}-01/questions.parquet"
    blob = bucket.blob(blob_path)
    blob.upload_from_file(buffer, content_type="application/octet-stream")
    
    print(f"✅ {blob_path} — {len(df_mois)} questions")

print("Bootstrap GCS terminé !")
