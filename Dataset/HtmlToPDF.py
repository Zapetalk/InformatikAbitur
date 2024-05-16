import os  # Package um mit Ordnern und Dateien zu arbeiten
from pyhtml2pdf import converter  # Package

FOLDER_HTML = 'C:\\Users\\joon\\PycharmProjects\\InformatikAbitur\\FinalData\\Html'  # Ordner mit den HTML Dateien
FOLDER_HTML_TO_PDF = 'C:\\Users\\joon\\PycharmProjects\\InformatikAbitur\\FinalData\\Pdf'  # Ordner in


# den die neuen PDFs kopiert werden sollen


# Funktion die alle HTML-Paths in einen Ordner speichert
def getHtmlFiles():
    html_files = []  # Ordner zum Speichern der HTML-Dateien
    for filename in os.listdir(FOLDER_HTML):  # Ruft jede einzelne Datei und Ordner in dem ausgewählten Ordner Path auf
        if os.path.isfile(os.path.join(FOLDER_HTML, filename)):  # Prüft, ob das Element eine Datei ist
            html_files.append(filename)  # Fügt den Datei-Path der Liste hinzu
    return html_files  # Gibt die Liste mit den Datei-Paths aus


html = getHtmlFiles()  # Ruft die Funktion auf und speichert die Liste
for file in html:  # Ruft alle Datei-Paths in der Liste einzeln auf
    # Speichert die HTML-Datei als neue PDF-Datei am neuen Ordner:
    converter.convert(os.path.join(FOLDER_HTML, file), os.path.join(FOLDER_HTML_TO_PDF, file.replace(".html", ".pdf")))
