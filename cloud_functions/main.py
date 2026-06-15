import json                          # librairie pour convertir des données en format JSON
import base64                        # librairie pour encoder/décoder des données en base64
from datetime import datetime, timedelta  # pour manipuler les dates (hier, aujourd'hui...)
from google.cloud import pubsub_v1, secretmanager  # librairies GCP pour Pub/Sub et Secret Manager
import requests                      # librairie pour faire des appels HTTP (appeler l'API)

def get_api_key():                   # définit la fonction qui récupère la clé API
    client = secretmanager.SecretManagerServiceClient()  # crée une connexion à Secret Manager
    name = "projects/stackoverflow-pipeline/secrets/stackoverflow-api-key/versions/latest"  # chemin vers la clé dans Secret Manager
    response = client.access_secret_version(request={"name": name})  # va chercher la clé
    return response.payload.data.decode("UTF-8")  # renvoie la clé en texte lisible

def fetch_questions(api_key):        # définit la fonction qui récupère les questions du jour
    yesterday = datetime.now() - timedelta(days=1)  # calcule la date d'hier
    
    url = "https://api.stackexchange.com/2.3/questions"  # l'adresse de l'API Stack Overflow
    all_questions = []               # liste vide qui va accumuler toutes les questions
    page = 1                         # on commence à la page 1
    has_more = True                  # tant qu'il y a des pages suivantes on continue
    
    while has_more:                  # boucle tant qu'il y a des questions à récupérer
        params = {                   # les paramètres qu'on envoie à l'API
            "fromdate": int(yesterday.timestamp()),    # date de début : hier
            "todate": int(datetime.now().timestamp()), # date de fin : maintenant
            "order": "desc",         # trier par ordre décroissant
            "sort": "creation",      # trier par date de création
            "site": "stackoverflow", # on veut les données de Stack Overflow
            "pagesize": 100,         # 100 questions par appel (maximum autorisé)
            "page": page,            # numéro de la page courante
            "key": api_key,          # notre clé API pour s'authentifier
            "filter": "withbody"     # inclut le contenu complet des questions
        }
        
        response = requests.get(url, params=params)  # appelle l'API
        data = response.json()                        # convertit la réponse en Python
        all_questions.extend(data.get("items", []))  # ajoute les questions à la liste
        has_more = data.get("has_more", False)        # vérifie s'il y a une page suivante
        page += 1                                     # passe à la page suivante
        
        print(f"Page {page} récupérée — {len(all_questions)} questions au total")  # affiche la progression
    
    return all_questions             # renvoie toutes les questions récupérées
    
    response = requests.get(url, params=params)  # appelle l'API avec ces paramètres
    return response.json().get("items", [])      # renvoie la liste des questions

def publish_to_pubsub(questions):    # définit la fonction qui envoie dans Pub/Sub
    publisher = pubsub_v1.PublisherClient()  # crée une connexion à Pub/Sub
    topic_path = "projects/stackoverflow-pipeline/topics/stackoverflow-questions"  # chemin vers notre topic

    for question in questions:       # pour chaque question récupérée
        message = json.dumps(question).encode("utf-8")  # convertit la question en bytes JSON
        publisher.publish(topic_path, message)           # envoie le message dans Pub/Sub
    
    print(f"{len(questions)} questions envoyées dans Pub/Sub")  # affiche le nombre de questions envoyées

def run(request):                    # point d'entrée — Google appelle cette fonction en premier
    print("Démarrage de l'ingestion quotidienne...")  # affiche un message de démarrage
    
    api_key = get_api_key()          # étape 1 : récupère la clé API
    questions = fetch_questions(api_key)  # étape 2 : récupère les questions du jour
    publish_to_pubsub(questions)     # étape 3 : envoie dans Pub/Sub
    
    return f"OK - {len(questions)} questions traitées"  # renvoie un message de succès