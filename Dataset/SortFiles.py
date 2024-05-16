import os  # Package um mit Ordnern und Dateien zu arbeiten
import shutil  # Package um Dateien zu koopieren

FOLDER_WEBSITE = 'C:\\Users\\joon\\PycharmProjects\\InformatikAbitur\\LeibnizWebsite090524'  # Ordner mit den Dateien der Website
FOLDER_HTML = 'C:\\Users\\joon\\PycharmProjects\\InformatikAbitur\\FinalData\\Html'  # Ordner in den die HTML
# Dateien kopiert werden sollen
FOLDER_PDF = 'C:\\Users\\joon\\PycharmProjects\\InformatikAbitur\\FinalData\\Pdf'  # Ordner in dem die PDF-Dateien
# kopiert werden sollen

files = []  # Liste zum Speichern der Datei-Path der Dateien von der Leibniz Website


# Recursive Funktion zum Speichern aller Datei-Paths im Ordner der Website
def searchFiles(path):
    for file in os.listdir(path):  # Ruft jede einzelne Datei und Ordner in dem ausgewählten Ordner Path auf
        if os.path.isfile(os.path.join(path, file)):  # Prüft, ob das Element eine Datei ist
            files.append(os.path.join(path, file))  # Fügt den Datei-Path der Liste hinzu
        else:
            searchFiles(os.path.join(path, file))  # Ruft die Funktion auf mit dem unterordner als neuen Haupt-Path


searchFiles(FOLDER_WEBSITE)  # Ruft die Funktion auf mit dem Ordner in dem die Dateien der Website liegen

print(f"Anzahl Dokumente: {len(files)}")  # Gibt die Anzahl der gefundenen Dokumente aus

html_count = 0  # Zählvariable für die Anzahl der HTML-Dateien
pdf_count = 0  # Zählvariable für die Anzahl der PDF-Dateien
for f in files:  # Ruft alle Datei-Path in der Liste auf
    file_ending = (f.title().split('.')[1])  # Speichert das Dateiende der Datei
    if file_ending == "Htm" or file_ending == "Html":  # Überprüft, ob das Dateiende htm oder html ist
        html_count += 1  # Aktualisiert den Zähler
        shutil.copy(f, FOLDER_HTML)  # Kopiert die Datei in den HTML-Ordner
    if file_ending == "Pdf":  # Überprüft, ob das Dateiende pdf ist
        pdf_count += 1  # Aktualisiert den Zähler
        shutil.copy(f, FOLDER_PDF)  # Kopiert die Datei in den PDF-Ordner

print(f"Anzahl PDFs: {pdf_count}")  # Gibt die Anzahl der PDF-Dokumente aus
print(f"Anzahl HTML Seiten: {html_count}")  # Gibt die Anzahl der HTML-Dokumente aus
