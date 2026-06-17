{{ config(materialized='table') }}

-- Evolution des langages autour des sorties de modèles IA
-- Répond à H4

SELECT
    DATE(creation_date) AS jour,
    tag AS langage,
    COUNT(*) AS nombre_questions
FROM `stackoverflow-pipeline.stackoverflow.questions_completes`,
UNNEST(SPLIT(tags, '|')) AS tag
WHERE tag IN ('python', 'javascript', 'java', 'c#', 'r', 'scala', 'rust')
AND DATE(creation_date) >= '2020-01-01'
GROUP BY jour, tag
ORDER BY jour
