<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") { //Abfrage ob der Server eine Request Method POST bekommen hat 
    $prompt = $_POST["prompt"]; // Speichern von der Frage

    $command = "python3 ChatBot.py " . escapeshellarg($prompt); // Formulierung eines Befehls der das Python Skript mit der Frage als Argument ausführt
    $output = shell_exec($command); // Führt den Befehl aus und Speichert den Output

    echo $output; // Gibt den Output zurück zur HTML-Seite
}
?>
