{{ config(materialized='table') }}

-- Nombre de questions par langage par mois
-- Répond à H1 (cycles de mode) et H2 (langages disparus)

WITH questions_avec_mois AS (
    SELECT
        DATE_TRUNC(creation_date, MONTH) AS mois,
        tag
    FROM {{ ref('questions_completes') }},
    UNNEST(SPLIT(tags, '|')) AS tag
    WHERE tags IS NOT NULL
),

langages_cibles AS (
    SELECT *
    FROM questions_avec_mois
    WHERE tag IN (
        'python', 'javascript', 'java', 'c#', 'c++', 'c',
        'typescript', 'php', 'ruby', 'swift', 'kotlin', 'rust',
        'go', 'scala', 'r', 'matlab', 'dart', 'lua',
        'haskell', 'elixir', 'clojure', 'erlang', 'julia',
        'html', 'css', 'sass', 'less',
        'sql', 'plsql', 'tsql',
        'perl', 'cobol', 'fortran', 'pascal', 'delphi',
        'vba', 'vb.net', 'visual-basic', 'assembly',
        'actionscript', 'flash', 'coffeescript',
        'objective-c', 'f#', 'groovy', 'smalltalk',
        'lisp', 'scheme', 'prolog', 'ada', 'forth',
        'bash', 'powershell', 'shell',
        'apex', 'abap', 'labview', 'ocaml'
    )
)

SELECT
    mois,
    tag AS langage,
    COUNT(*) AS nombre_questions
FROM langages_cibles
GROUP BY mois, tag
ORDER BY mois ASC, nombre_questions DESC
