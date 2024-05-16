import kfp.dsl as dsl
from kfp import compiler
from typing import Dict, List


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['appengine-python-standard']
)
# Gibt alle Dateien die Gefunden werden sollen aus
def getMatchingFiles(directory: str) -> List[str]:
    import os  # Package zum Arbeiten mit Dateien und Ordern

    matching_files = []  # Liste zum Speichern der Datei-Paths
    # Suche nach allen Dateien im Google Cloud Storage(GCS) Bucket-Path für os.walk muss der Path umgeschrieben werden:
    for root, files in os.walk(directory.replace("gs://", "/gcs/")):
        for file in files:  # Ruft jede Datei einzeln auf
            # Fügt den Datei-Path der Liste hinzu und verändert die Schreibweise wieder zu gs://
            matching_files.append(os.path.join(root, file).replace("/gcs/", "gs://"))

    return matching_files  # Gibt die Liste an Dateien aus


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['pypdf2==2.12.1', 'appengine-python-standard']
)
# Teilt ein PDF in einzelne Seiten auf und speichert diese in einem neuen Ordner
def splitIntoPages(pdf_file: str) -> List[str]:
    import os  # Package zum Arbeiten mit Dateien und Ordern
    import PyPDF2  # Package zum Arbeiten mit PDFs

    page_files = []  # Liste mit den jeweiligen Datei-Paths des PDFs

    # Öffnet die Datei im Lese und binären Modus:
    with open(pdf_file.replace("gs://", "/gcs/"), 'rb') as file:
        pdf_reader = PyPDF2.PdfFileReader(file)  # Erstellt ein Objekt zum Lesen der Datei
        total_pages = pdf_reader.numPages  # Gibt die Anzahl an Seiten an

        # Zählschleife mit der Anzahl an Seiten:
        for page_number in range(total_pages):
            pdf_page = pdf_reader.getPage(page_number)  # Liest die aktuelle Seite
            pdf_writer = PyPDF2.PdfFileWriter()  # Erstellt ein Objekt zum Schreiben von Dateien
            pdf_writer.addPage(pdf_page)  # Fügt eine Seite dem neuen Dokument hinzu
            # Erstellt einen neuen Ordner mit dem Namen des PDFs, falls er noch nicht existiert
            os.makedirs(
                os.path.dirname(pdf_file.replace("gs://", "/gcs/").replace(".pdf", "/")),
                exist_ok=True
            )
            # Variable mit den Kompletten Dateien-Path der PDF-Seite inklusive Dateinamen:
            output_file_path = pdf_file.replace("gs://", "/gcs/").replace(".pdf", "/") + \
                               pdf_file.split("/")[-1].replace(".pdf", f".{page_number + 1}.pdf")
            # Öffnet den Dateien-Path im Schreiben und binären Modus:
            with open(output_file_path, 'wb') as output_file:
                pdf_writer.write(output_file)  # Erstellt die Datei
            page_files.append(output_file_path.replace("/gcs/", "gs://"))  # Fügt die Datei der Liste hinzu

    return page_files  # Gibt die Liste mit den Datei-Paths der Seiten aus


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['google-cloud-documentai', 'appengine-python-standard']
)
# Bearbeitet den PDF-File mithilfe des Document-AI Processors und speichert das ergebnis als txt-Datei:
def parseText(pdf_file: str) -> str:
    from google.cloud import documentai  # Package zum Arbeiten mit DocumentAI
    from google.api_core.client_options import ClientOptions  # Package zum Verbinden mit Google Cloud

    # Project Variablen:
    project_id = 'joonaltmanninformatikabitur'
    location = 'eu'
    mime_type = 'application/pdf'
    processor_id = '81d1ffce46ea3308'

    # Verbindung mit dem Document-Ai Processor in der Google Cloud
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(project_id, location, processor_id)

    # Öffnet die Datei im Lese und binären Modus:
    with open(pdf_file.replace("gs://", "/gcs/"), "rb") as read_file:
        file_content = read_file.read()  # Liest und speichert den Inhalt des PDF-Dokuments
    # Fügt die Datei und die Datei-Art zusammen:
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)
    # Fügt die Anfrage an den Processor zusammen:
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    # Führt die Anfrage aus:
    result = client.process_document(request=request)
    # Speichert das Ergebnis:
    document = result.document
    # Öffnet den Dateien-Path im SchreibenModus:
    with open(pdf_file.replace("gs://", "/gcs/").replace(".pdf", ".txt"), 'w') as file:
        file.write(document.text)  # Erstellt die Datei als txt miz dem Ergebnis der Anfrage
    return pdf_file.replace(".pdf", ".txt")  # Gibt die Textvariante der Datei aus


# Gibt an welche Interpreter und welche Packages benutzt werden
@dsl.component(
    base_image='python:3.11',
    packages_to_install=['google-cloud-aiplatform', 'appengine-python-standard']
)
# Erstellt Multidimensionale Embeddings aus einer Text-Datei
def generateEmbedding(txt_file: str) -> Dict:
    from vertexai.language_models import TextEmbeddingModel  # Package für Google AIs

    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")  # Ruft das Model auf

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
        hosts=["http://10.156.0.9:9200"],  # Lokale IP-Adresse im Netzwerk
        basic_auth=("elastic", "1laBg6rS87g4mBBh61l96Ax6")  # Voreingestellter default user + password
    )

    index_name = "leibniz_website"  # Name unter dem die Embeddings gespeichert werden

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
            parallelism=3
    ) as pdf_file:
        # Teilt das Dokument in einzelne Seiten
        split_pdf_into_pages_task = splitIntoPages(
            pdf_file=pdf_file
        )
        # Iteriert durch alle PDF-Seiten
        with dsl.ParallelFor(
                name="pdf-page-parsing",
                items=split_pdf_into_pages_task.output,
                parallelism=3
        ) as pdf_page_file:
            # Bearbeitet die Seite mit Dokument AI
            parse_text_task = parseText(
                pdf_file=pdf_page_file
            )
            # Erstellt die Embeddings zur Seite
            generate_embedding_task = generateEmbedding(
                txt_file=parse_text_task.output
            )
            # Speichert die Embeddings
            write_embeddings_task = write_embeddings(
                embedding=generate_embedding_task.output
            )


# Compiled die Pipline in ein json Dokument:
compiler.Compiler().compile(leibnizWebsite, 'leibnizpipeline2.json')  # Compiles
