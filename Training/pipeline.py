import kfp.dsl as dsl
from kfp import compiler
from typing import Dict, List


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['appengine-python-standard', 'kfp']
)
# Gibt alle Dateien die Gefunden werden sollen aus
def getMatchingFiles(directory: str) -> List[str]:
    import os  # Package zum Arbeiten mit Dateien und Ordern

    matching_files = []  # Liste zum Speichern der Datei-Paths
    # Suche nach allen Dateien im Google Cloud Storage(GCS) Bucket-Path für os.walk muss der Path umgeschrieben werden:
    for root,dirs, files in os.walk(directory.replace("gs://", "/gcs/")):
        for file in files:  # Ruft jede Datei einzeln auf
            # Fügt den Datei-Path der Liste hinzu und verändert die Schreibweise wieder zu gs://
            matching_files.append(os.path.join(root, file).replace("/gcs/", "gs://"))

    return matching_files  # Gibt die Liste an Dateien aus



# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['google-cloud-aiplatform', 'appengine-python-standard']
)
# Fasst das PDF-Zusammen und speichert das Ergebnis in einer Text Datei:
def summarizeText(pdf_file: str) -> str:
    from vertexai.generative_models import GenerativeModel, Part # Package für Google AIs

    
    model = GenerativeModel(model_name="gemini-1.5-pro-preview-0514") # Initiiert Gemini1.5

    # Die Prompt die bei Google Gemini ausgeführt wird:
    prompt = """
    Du bist Proffesionel im Zusammenfassen von Dokumenten.
    Bitte fasse das gegebene Dokument zusammen. Ignoriere die nicht zum Hauptthema passenden Informationen
    """

    
    pdf_file_content = Part.from_uri(pdf_file, mime_type="application/pdf") # Bereitet das Abschicken von der PDF-Datei vor
    contents = [pdf_file_content, prompt] # Verbindet die Prompt und die PDF-Datei

    response = model.generate_content(contents) # Schickt die Anfrage an die KI und speichert die Antwort
    
    with open(pdf_file.replace("gs://", "/gcs/").replace(".pdf", ".txt"), 'w') as file:
        file.write(response.text)  # Erstellt die Datei als txt miz dem Ergebnis der Anfrage
    return pdf_file.replace(".pdf", ".txt")  # Gibt die Textvariante der Datei aus


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['google-cloud-aiplatform', 'appengine-python-standard']
)
# Erstellt Multidimensionale Embeddings aus einer Text-Datei
def generateEmbedding(txt_file: str) -> Dict:
    from vertexai.language_models import TextEmbeddingModel  # Package für Google AIs

    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")  # Ruft das Model auf

    # Öffnet die Datei im lese Modus:
    with open(txt_file.replace("gs://", "/gcs/"), 'r') as f:
        text = f.read()  # Speichert den Inhalt der Datei
        embeddings = model.get_embeddings([text])  # Generiert die Embeddings aus dem Text der Datei
        embedding = embeddings[0].values  # Speichert den ersten Eintrag der Liste an Embeddings

    return {"id": txt_file, "embedding": embedding}  # Gibt ein Dictonary aus bei dem die id = Den Namen der Datei und
    # embedding = dem embedding der Datei


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['elasticsearch', 'appengine-python-standard']
)
# Speichert die Embeddings in der Elastic Cloud
def write_embeddings(embedding: Dict):
    from elasticsearch import Elasticsearch  # Package zum Speichern und Suchen von Embeddings

    # Connection Details zur Elastic
    es = Elasticsearch(
        hosts=["http://10.156.15.221:9200"],  # Lokale IP-Adresse im Netzwerk
        basic_auth=("elastic", "4n7v79WY49CkZmD16AWB7zr7")  # Voreingestellter default user + password
    )

    index_name = "leibniz_website_summary"  # Name unter dem die Embeddings gespeichert werden

    # Gibt an was für ein Typ an embedding hier ausgegeben wird:
    mapping = {
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768
                }
            }
        }
    }

    # Erstellt den Namen unter dem das ganze gespeichert wird
    es.indices.create(index=index_name, body=mapping, ignore=400)

    # Speichert das Embedding auf der Elastic Cloud
    es.index(index=index_name, id=embedding["id"], body={"embedding": embedding["embedding"]})


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.pipeline(
    name="leibniz_website",
)
# Packt die Funktionen zusammen
def leibnizWebsite(gcs_directory: str):
    # Sucht alle relevanten Dokumente auf
    get_matching_files_task = getMatchingFiles(
        directory=gcs_directory
    )
    # Iteriert durch alle PDF-Dokumente
    with dsl.ParallelFor(
            name="pdf-parsing",
            items=get_matching_files_task.output,
            parallelism=10
    ) as pdf_file:
        # Fasst die PDF-Seite zusammen
        summarize_text_task = summarizeText(
            pdf_file=pdf_file
        )
        # Erstellt die Embeddings zur Seite
        generate_embedding_task = generateEmbedding(
            txt_file=summarize_text_task.output
        )
        # Speichert die Embeddings
        write_embeddings_task = write_embeddings(
            embedding=generate_embedding_task.output
        )


# Compiled die Pipline in ein json Dokument:
compiler.Compiler().compile(leibnizWebsite, 'leibnizpipelinesummary.json') 
