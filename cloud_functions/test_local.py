from main import get_api_key, fetch_questions, publish_to_pubsub

print("=== TEST 1 : Secret Manager ===")
api_key = get_api_key()
print(f"✅ Clé API récupérée : {api_key[:5]}...")  # affiche juste les 5 premiers caractères

print("\n=== TEST 2 : API Stack Overflow ===")
questions = fetch_questions(api_key)
print(f"✅ {len(questions)} questions récupérées")
if questions:
    print(f"Exemple : {questions[0]['title']}")  # affiche le titre de la première question

print("\n=== TEST 3 : Pub/Sub ===")
publish_to_pubsub(questions[:5])  # envoie juste 5 questions pour tester
print("✅ Questions envoyées dans Pub/Sub")