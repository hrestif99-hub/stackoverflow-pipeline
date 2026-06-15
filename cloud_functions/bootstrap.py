from google.cloud import bigquery

# Connexion à BigQuery
client = bigquery.Client(project="stackoverflow-pipeline")

# La requête qui copie les données du dataset public vers le nôtre
query = """
CREATE OR REPLACE TABLE `stackoverflow-pipeline.stackoverflow.questions` AS
SELECT
    id,
    title,
    creation_date,
    tags,
    answer_count,
    comment_count,
    favorite_count,
    score,
    accepted_answer_id,
    last_activity_date
FROM `bigquery-public-data.stackoverflow.posts_questions`
WHERE creation_date >= '2008-01-01'
"""

print("Démarrage du bootstrap historique...")
job = client.query(query, location="US")
job.result()  # attend que la requête soit terminée
print("Bootstrap terminé ! Les données sont dans BigQuery.")