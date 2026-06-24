import requests
import time
import psycopg2
import os
import json
from datetime import datetime
from google.cloud import secretmanager
from dotenv import load_dotenv
load_dotenv()

CHECKPOINT_FILE = "scripts/checkpoint.json"

def charger_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return []

def sauvegarder_checkpoint(langages_faits):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(langages_faits, f)

def recuperer_cle_api():
    client = secretmanager.SecretManagerServiceClient()
    nom = "projects/stackoverflow-pipeline/secrets/stackoverflow-api-key/versions/latest"
    response = client.access_secret_version(request={"name": nom})
    return response.payload.data.decode("UTF-8")

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    database=os.environ.get("POSTGRES_DB", "stackoverflow"),
    user=os.environ.get("POSTGRES_USER", "airflow"),
    password=os.environ.get("POSTGRES_PASSWORD", "airflow"),
    port=os.environ.get("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

API_KEY = recuperer_cle_api()

DEBUT = 1664085392  # 25 septembre 2022
FIN   = 1781686510  # 17 juin 2026

LANGAGES = [
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
]

def recuperer_questions_par_tag(tag, page):
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        "page": page,
        "pagesize": 100,
        "fromdate": DEBUT,
        "todate": FIN,
        "order": "asc",
        "sort": "creation",
        "tagged": tag,
        "site": "stackoverflow",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200 or not response.text.strip():
        print(f"Réponse inattendue : status={response.status_code}")
        return {"items": [], "has_more": False, "quota_remaining": 0}
    return response.json()

def inserer_dans_postgres(questions):
    inseres = 0
    ignores = 0
    for q in questions:
        try:
            cursor.execute("""
                INSERT INTO questions
                    (id, title, creation_date, tags, score, answer_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                q.get("question_id"),
                q.get("title"),
                datetime.utcfromtimestamp(q.get("creation_date")),
                "|".join(q.get("tags", [])),
                q.get("score", 0),
                q.get("answer_count", 0)
            ))
            inseres += 1
        except Exception as e:
            print(f"Erreur : {e}")
            ignores += 1
    conn.commit()
    return inseres, ignores

total = 0

langages_faits = charger_checkpoint()
print(f"Checkpoint chargé — {len(langages_faits)} langages déjà traités : {langages_faits}")

for langage in LANGAGES:
    if langage in langages_faits:
        print(f"--- {langage} déjà traité, on passe ---")
        continue

    print(f"\n--- Récupération de : {langage} ---")
    page = 1
    total_langage = 0

    while True:
        data = recuperer_questions_par_tag(langage, page)
        questions = data.get("items", [])

        if not questions:
            break

        inseres, ignores = inserer_dans_postgres(questions)
        total_langage += inseres
        total += inseres
        print(f"Page {page} — {inseres} insérées — Total {langage} : {total_langage}")

        if not data.get("has_more", False):
            break

        remaining = data.get("quota_remaining", 999)
        print(f"Quota restant : {remaining}")
        if remaining < 10:
            print("Quota épuisé ! On s'arrête.")
            cursor.close()
            conn.close()
            exit()

        page += 1
        time.sleep(0.2)

    # Langage terminé — on sauvegarde le checkpoint
    langages_faits.append(langage)
    sauvegarder_checkpoint(langages_faits)
    print(f"✓ {langage} terminé — {total_langage} questions insérées")

cursor.close()
conn.close()
print(f"\nBootstrap terminé — {total} questions insérées au total")