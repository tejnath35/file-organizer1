import os
import shutil
import json
from flask import Flask, render_template, request, redirect, flash

app = Flask(__name__)
app.secret_key = "secretkey"

FILE_TYPES = {
    'Documents': ['.pdf', '.docx', '.txt', '.xlsx', '.pptx'],
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'Audio': ['.mp3', '.wav', '.aac'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv'],
    'Archives': ['.zip', '.rar', '.tar', '.gz'],
    'Scripts': ['.py', '.js', '.cpp', '.java', '.html', '.css'],
    'Others': []
}

UNDO_LOG_FILE = "undo_log.json"


def get_category(extension):
    for category, extensions in FILE_TYPES.items():
        if extension.lower() in extensions:
            return category
    return 'Others'


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/organize", methods=["POST"])
def organize():
    path = request.form["folder"]

    if not os.path.isdir(path):
        flash("Invalid folder path!")
        return redirect("/")

    file_moves = []
    count = 0

    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)

        if os.path.isfile(file_path):
            _, ext = os.path.splitext(filename)
            category = get_category(ext)

            target_dir = os.path.join(path, category)
            os.makedirs(target_dir, exist_ok=True)

            new_path = os.path.join(target_dir, filename)

            if os.path.abspath(file_path) == os.path.abspath(new_path):
                continue

            if filename.startswith("~") or filename.startswith("."):
                continue

            try:
                shutil.move(file_path, new_path)
                file_moves.append({"from": new_path, "to": file_path})
                count += 1
            except PermissionError:
                print(f"Skipping locked file: {filename}")
                continue


    with open(UNDO_LOG_FILE, "w") as f:
        json.dump(file_moves, f)

    flash(f"Organized {count} files successfully!")
    return redirect("/")


@app.route("/undo")
def undo():
    if not os.path.exists(UNDO_LOG_FILE):
        flash("No undo log found.")
        return redirect("/")

    with open(UNDO_LOG_FILE, "r") as f:
        file_moves = json.load(f)

    restored = 0

    for move in file_moves:
        if os.path.exists(move["from"]):
            os.makedirs(os.path.dirname(move["to"]), exist_ok=True)
            shutil.move(move["from"], move["to"])
            restored += 1

    os.remove(UNDO_LOG_FILE)

    flash(f"Restored {restored} files.")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
