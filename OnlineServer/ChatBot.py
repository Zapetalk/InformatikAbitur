# coding=UTF-8
from elasticsearch import Elasticsearch  # Package zum Speichern und Suchen von Embeddings
from google.cloud import storage  # Importiert das Arbeiten mit der Google Cloud Storage
from google.cloud import aiplatform  # Importiert das Arbeiten mit der Google AI
from vertexai.language_models._language_models import TextEmbeddingModel, TextGenerationModel  # Importiert das
# Arbeiten mit den Modellen
import os  # Package um mit Ordnern und Dateien zu arbeiten
import sys  # Package um mit dem System zu integrieren


# Funktion zum Herunterladen von Dateien
def download_blob(bucket_name, source_blob_name):
    storage_client = storage.Client()  # Initiiert einen Client
    bucket = storage_client.bucket(bucket_name)  # Definiert den Cloud Storage Bucket
    blob = bucket.blob(source_blob_name)  # Definiert den Inhalt
    return blob.download_as_text() # Lädt den Inhalt als Text herunter


# Anmeldung in der Google Cloud:
aiplatform.init(project='leibnizchat', location='europe-west3')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'leibnizchat.json'

# Initiiert das Text Embedding Model
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

# Initiiert die übergebene Prompt
PROMPT = sys.argv[1]

# Verbindung mit Elasticsearch
es = Elasticsearch(
    hosts=["http://10.156.15.221:9200"],
    basic_auth=("elastic", "4n7v79WY49CkZmD16AWB7zr7")
)

# Name unter dem die Embeddings gespeichert wurden
index_name = 'leibniz_website'

# Speichert die Embeddings der Prompt
embeddings = model.get_embeddings([PROMPT])

# Bereitet die Anfrage an Elasticsearch
script_query = {
    "script_score": {
        "query": {"match_all": {}},
        "script": {
            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
            "params": {"query_vector": embeddings[0].values}
        }
    }
}

# Führt die Elasticsearch durch
res = es.search(index=index_name, query=script_query)


bucket_name = "leibnizchat-storage"  # Der Name des GCS Buckets

# Das Ergebnis der Elasticsearch in die Dateien die zu herunterladen sind speichern:
source_blob_name = res["hits"]["hits"][0]['_id'].replace("gs://", "").replace(bucket_name + "/", "")

# Lädt die Dateien als Text herunter
text_content = download_blob(bucket_name, source_blob_name)

# Parameters zum Verhalten der KI:
parameters = {
    "temperature": 0.2,  # Definiert wie sicher die KI sich sein muss
    "max_output_tokens": 1024,  # Definiert die maximale Länge der Ausgabe
    "top_p": 0.8,  # Wie richtig sollen die KI mehrere Token auswählen
    "top_k": 40  # Wie richtig sollen die KI einzelnen Token auswählen
}

# Baut die Prompt und den Context mittels Prompt design zusammen
prompt = """
Beantworte die folgende Frage, sollte sie zu den Themenbereich einer Schule passen:""" + PROMPT + """
Falls die Frage nicht passt antworte mit: "Diese Frage befindet sich außerhalb meines Themenbereiches"

Falls es Hilft benutze diese Information zum beantworten der Frage:""" + text_content

# Initiiert das Text Generation Model:
model = TextGenerationModel.from_pretrained("text-bison@002")

# Generiert die Ausgabe:
response = model.predict(prompt, **parameters)

# Gibt die Aussage aus:
#print(f"Prompt: {prompt}\n\n")
#print(f"Response from Model: {response.text}")
print(response.text)