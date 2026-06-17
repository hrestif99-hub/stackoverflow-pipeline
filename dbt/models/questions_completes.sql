{{ config(materialized='table') }}

-- Combine l'historique BigQuery et les nouvelles questions quotidiennes

WITH historique AS (
    SELECT
        id,
        title,
        creation_date,
        tags,
        score,
        answer_count
    FROM `stackoverflow-pipeline.stackoverflow.questions`  -- table historique
),

nouvelles AS (
    SELECT
        id,
        title,
        creation_date,
        tags,
        score,
        answer_count
    FROM `stackoverflow-pipeline.stackoverflow.questions_lake`  -- nouvelles questions via GCS
),

toutes_les_questions AS (
    SELECT * FROM historique
    UNION ALL
    SELECT * FROM nouvelles
)

SELECT * FROM toutes_les_questions