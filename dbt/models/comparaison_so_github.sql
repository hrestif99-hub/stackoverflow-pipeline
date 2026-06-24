{{ config(materialized='table') }}

-- GOLD : croise deux signaux Silver pour répondre à H3/H4/H5
-- Signal 1 : questions posées sur Stack Overflow (evolution_langages_par_annee)
-- Signal 2 : code réellement écrit sur GitHub (github_activite)
-- Objectif : distinguer un vrai déclin d'un langage d'un simple effet
-- "moins besoin de poser la question" lié à l'essor de l'IA

WITH so AS (
    SELECT
        DATE(mois) AS mois,
        LOWER(langage) AS langage,
        nombre_questions
    FROM {{ ref('evolution_langages_par_annee') }}
),

github AS (
    SELECT
        mois,
        LOWER(langage) AS langage,
        nb_push
    FROM {{ source('stackoverflow', 'github_activite') }}
)

SELECT
    COALESCE(so.mois, github.mois) AS mois,
    COALESCE(so.langage, github.langage) AS langage,
    so.nombre_questions,
    github.nb_push
FROM so
FULL OUTER JOIN github
    ON so.langage = github.langage
    AND so.mois = github.mois
ORDER BY mois, langage