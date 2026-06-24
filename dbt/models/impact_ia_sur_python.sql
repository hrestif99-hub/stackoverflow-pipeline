{{ config(materialized='table') }}

-- Evolution quotidienne de Python depuis 2017
-- Répond à H3 : l'essor de l'IA a-t-il favorisé Python ?

SELECT
    DATE(creation_date) AS jour,
    COUNT(*) AS nombre_questions
FROM {{ ref('questions_completes') }},
UNNEST(SPLIT(tags, '|')) AS tag
WHERE tag = 'python'
AND DATE(creation_date) >= '2017-01-01'
GROUP BY jour
ORDER BY jour