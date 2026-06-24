{{ config(materialized='table') }}

-- Volume global de questions par jour depuis 2017
-- Répond à H5 : l'essor de l'IA a-t-il augmenté ou diminué le nombre de questions ?

SELECT
    DATE(creation_date) AS jour,
    COUNT(*) AS nombre_questions
FROM {{ ref('questions_completes') }}
WHERE DATE(creation_date) >= '2017-01-01'
GROUP BY jour
ORDER BY jour
