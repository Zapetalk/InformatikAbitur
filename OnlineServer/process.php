<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $prompt = $_POST["prompt"];

    $command = "ChatBot.py " . escapeshellarg($inputString);
    $output = shell_exec($command);

    echo $output;
}
?>