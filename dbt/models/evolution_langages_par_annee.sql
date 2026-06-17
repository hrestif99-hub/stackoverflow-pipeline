{{ config(materialized='table') }}

-- Nombre de questions par langage par année
-- Liste exhaustive de langages (actuels + disparus)
-- Répond à H1 (cycles de mode) et H2 (langages disparus)

WITH questions_avec_annee AS (
    SELECT
        EXTRACT(YEAR FROM creation_date) AS annee,
        tag
    FROM `stackoverflow-pipeline.stackoverflow.questions_completes`,
    UNNEST(SPLIT(tags, '|')) AS tag
    WHERE tags IS NOT NULL
),

langages_cibles AS (
    SELECT *
    FROM questions_avec_annee
    WHERE tag IN (
        -- Langages actuels populaires
        'python', 'javascript', 'java', 'c#', 'c++', 'c',
        'typescript', 'php', 'ruby', 'swift', 'kotlin', 'rust',
        'go', 'scala', 'r', 'matlab', 'dart', 'lua',
        'haskell', 'elixir', 'clojure', 'erlang', 'julia',

        -- Langages web
        'html', 'css', 'sass', 'less',

        -- Langages de données
        'sql', 'plsql', 'tsql',

        -- Langages historiques / disparus
        'perl', 'cobol', 'fortran', 'pascal', 'delphi',
        'vba', 'vb.net', 'visual-basic', 'assembly',
        'actionscript', 'flash', 'coffeescript',
        'objective-c', 'f#', 'groovy', 'smalltalk',
        'lisp', 'scheme', 'prolog', 'ada', 'forth',

        -- Shells et scripts
        'bash', 'powershell', 'shell',

        -- Autres
        'apex', 'abap', 'labview', 'ocaml'
    )
)

SELECT
    annee,
    tag AS langage,
    COUNT(*) AS nombre_questions
FROM langages_cibles
GROUP BY annee, tag
ORDER BY annee, nombre_questions DESC