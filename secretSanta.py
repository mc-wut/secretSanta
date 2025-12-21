"""
This is a secertSanta sorter for the family, it is designed with the 
following criteria in mind
1. Automatic Sorting on January 1
2. No getting your spouse
3. Minimal overlap of previous recipients
"""

import json
import os
import random
import tempfile
from datetime import datetime
from flask import Flask, request, session, redirect, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

# =====================
# CONFIG
# =====================

DATA_FILE = "data.json"
EXCLUSION_WINDOW = 4

# CHANGE THIS
SECRET_KEY = "CHANGE_ME_TO_RANDOM_STRING"

# Permanent exclusions (e.g. spouses)
PERMANENT_EXCLUSIONS = {
    "ruthie": {"tom"},
    "matt": {"stacy"},
    "tom": {"ruthie"},
    "stacy": {"matt"},
    "bob": set(),
    "eddie": set(),
    "maggie": set()
}

# =====================
# FILE I/O
# =====================

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    fd, temp = tempfile.mkstemp()
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(temp, DATA_FILE)

# =====================
# ASSIGNMENT LOGIC
# =====================

def build_exclusions(data):
    ids = list(data["participants"].keys())
    exclusions = {i: {i} for i in ids}

    # Permanent exclusions
    for giver, banned in PERMANENT_EXCLUSIONS.items():
        exclusions[giver].update(banned)

    # Rolling history exclusions
    years = sorted(
        (int(y) for y in data["history"].keys()),
        reverse=True
    )[:EXCLUSION_WINDOW]

    for y in years:
        for giver, receiver in data["history"][str(y)].items():
            exclusions[giver].add(receiver)

    return ids, exclusions

def validate_exclusions(ids, exclusions):
    for giver in ids:
        if len(exclusions[giver]) >= len(ids):
            raise RuntimeError(f"{giver} has no valid recipients")

def assign(ids, exclusions):
    assignments = {}
    used = set()
    random.shuffle(ids)

    def backtrack(i):
        if i == len(ids):
            return True

        giver = ids[i]
        for receiver in ids:
            if receiver in used:
                continue
            if receiver in exclusions[giver]:
                continue

            assignments[giver] = receiver
            used.add(receiver)

            if backtrack(i + 1):
                return True

            used.remove(receiver)
            del assignments[giver]

        return False

    if not backtrack(0):
        raise RuntimeError("No valid assignment found")

    return assignments

def run_yearly_assignment():
    data = load_data()
    year = str(datetime.now().year)

    if year in data["assignments"]:
        return  # already assigned

    ids, exclusions = build_exclusions(data)
    validate_exclusions(ids, exclusions)
    assignments = assign(ids, exclusions)

    data["assignments"][year] = assignments
    data["history"][year] = assignments
    save_data(data)

# =====================
# FLASK APP
# =====================

app = Flask(__name__)
app.secret_key = SECRET_KEY

LOGIN_TEMPLATE = """
<h2>Secret Santa Login</h2>
<form method="post">
  <input name="username" placeholder="Name" required>
  <input name="password" type="password" placeholder="Password" required>
  <button type="submit">Login</button>
  {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
</form>
"""

ASSIGNMENT_TEMPLATE = """
<h1>🎅 Secret Santa</h1>
<p>You are buying a gift for:</p>
<h2>{{ recipient }}</h2>
<a href="/logout">Logout</a>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    data = load_data()

    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        entry = data["participants"].get(user)
        if entry and check_password_hash(entry["password_hash"], pw):
            session["user"] = user
            return redirect("/assignment")

        return render_template_string(LOGIN_TEMPLATE, error="Invalid login")

    return render_template_string(LOGIN_TEMPLATE)

@app.route("/assignment")
def assignment_view():
    if "user" not in session:
        return redirect("/")

    run_yearly_assignment()

    data = load_data()
    year = str(datetime.now().year)
    giver = session["user"]
    receiver_id = data["assignments"][year].get(giver)
    receiver = data["participants"][receiver_id]["display"]

    return render_template_string(ASSIGNMENT_TEMPLATE, recipient=receiver)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run()