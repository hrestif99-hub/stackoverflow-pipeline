from unittest.mock import patch, MagicMock
from main import publish_to_pubsub
from main import publish_to_pubsub, fetch_questions

@patch('main.pubsub_v1.PublisherClient')
def test_publish_to_pubsub_envoie_chaque_question(mock_publisher_class):
    # On crée un faux client Pub/Sub
    mock_publisher_instance = MagicMock()
    mock_publisher_class.return_value = mock_publisher_instance

    # Données fictives : 3 fausses questions
    questions_fictives = [
        {"title": "Question 1"},
        {"title": "Question 2"},
        {"title": "Question 3"},
    ]

    publish_to_pubsub(questions_fictives)

    # On vérifie que publish() a été appelé exactement 3 fois (une par question)
    assert mock_publisher_instance.publish.call_count == 3

@patch('main.requests.get')
def test_fetch_questions_retourne_les_questions(mock_get):
    # On simule une fausse réponse HTTP de l'API Stack Exchange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [{"title": "Question test"}],
        "has_more": False
    }
    mock_get.return_value = mock_response

    resultat = fetch_questions("fausse-cle-api")

    assert len(resultat) == 1
    assert resultat[0]["title"] == "Question test"
