from flask import Flask, render_template_string
import pandas as pd
import datetime
import json
import os

# Load glossary
df = pd.read_csv("PM_Glossary_Fixed.csv")
HISTORY_FILE = "shown_history.json"
app = Flask(__name__)

# HTML Template
BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; overflow-x: hidden; }

      :root {
        --bg-color: #f9fafb;
        --text-color: #1f2937;
        --card-bg: #ffffff;
        --highlight: #2563eb;
      }

      body.dark {
        --bg-color: #111827;
        --text-color: #f3f4f6;
        --card-bg: #1f2937;
        --highlight: #3b82f6;
      }

      body {
        background: var(--bg-color);
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
        transition: background 0.3s ease, color 0.3s ease;
      }

      .container {
        background: var(--card-bg);
        padding: 2rem 2.5rem;
        margin-top: 3rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        max-width: 800px;
        width: 100%;
        animation: fadeIn 1s ease-out;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }

      h1 {
        font-size: 2rem;
        margin-bottom: 1.2rem;
        text-align: center;
      }

      .concept {
        font-size: 1.4rem;
        color: var(--highlight);
        font-weight: 600;
        text-align: center;
        margin-bottom: 1rem;
      }

      .definition {
        font-size: 1.05rem;
        line-height: 1.6;
        text-align: justify;
        margin-top: 0.5rem;
        display: none;
      }

      .definition.visible { display: block; }
      .definition.static { display: block; }

      footer {
        margin-top: 2rem;
        text-align: center;
        font-size: 0.9rem;
        opacity: 0.6;
        width: 100%;
      }

      .topbar {
        width: 100%;
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 800px;
        box-sizing: border-box;
      }

      .nav-links a {
        color: var(--highlight);
        margin: 0 1rem;
        text-decoration: none;
        font-weight: 500;
      }

      .dark-toggle {
        cursor: pointer;
        padding: 0.5rem 1rem;
        border: 1px solid var(--highlight);
        border-radius: 6px;
        background: transparent;
        color: var(--highlight);
        font-size: 0.9rem;
      }

      .search-box {
        margin: 1rem auto 2rem;
        max-width: 100%;
        width: 100%;
        text-align: center;
      }

      .search-box input {
        width: 100%;
        padding: 0.6rem 1rem;
        font-size: 1rem;
        border: 1px solid #ccc;
        border-radius: 8px;
        outline: none;
      }

      .library-list { margin-top: 1rem; }
      .library-item {
        margin-bottom: 1.5rem;
        cursor: pointer;
      }
      .library-item h3 {
        color: var(--highlight);
        margin-bottom: 0.3rem;
      }

      .hidden { display: none !important; }
    </style>
    <script>
      function toggleDarkMode() {
        document.body.classList.toggle("dark");
        localStorage.setItem("darkMode", document.body.classList.contains("dark"));
      }

      function toggleDefinition(id) {
        const el = document.getElementById(id);
        el.classList.toggle("visible");
      }

      function filterConcepts() {
        const input = document.getElementById("searchInput").value.toLowerCase();
        const items = document.getElementsByClassName("library-item");
        for (let item of items) {
          const title = item.querySelector("h3").innerText.toLowerCase();
          item.style.display = title.includes(input) ? "block" : "none";
        }
      }

      window.onload = () => {
        if (localStorage.getItem("darkMode") === "true") {
          document.body.classList.add("dark");
        }
      }
    </script>
  </head>
  <body>
    <div class="topbar">
      <div class="nav-links">
        <a href="/">📘 Daily</a>
        <a href="/library">📚 Library</a>
      </div>
      <button class="dark-toggle" onclick="toggleDarkMode()">🌓 Toggle Dark Mode</button>
    </div>

    <div class="container">
      <h1>{{ heading }}</h1>
      {% if concept %}
        <div class="concept">{{ concept }}</div>
      {% endif %}
      {% if definition %}
        {{ definition|safe }}
      {% endif %}
      {{ extra|safe }}
    </div>

    <footer>Product Management Glossary App · Made with ❤️</footer>
  </body>
</html>
"""

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

@app.route("/")
def daily_concept():
    today = datetime.date.today().isoformat()
    history = load_history()

    if len(set(history.values())) >= len(df):
        history = {}

    if today in history:
        concept = history[today]
        row = df[df["Concept"] == concept].iloc[0]
    else:
        shown_concepts = set(history.values())
        available_df = df[~df["Concept"].isin(shown_concepts)]
        row = available_df.sample(n=1).iloc[0]
        history[today] = row["Concept"]
        save_history(history)

    return render_template_string(
        BASE_TEMPLATE,
        title="Daily Product Concept",
        heading="📘 Daily Product Concept",
        concept=row["Concept"],
        definition=f"<div class='definition static'>{row['Definition']}</div>",
        extra=""
    )

@app.route("/library")
def library():
    items = ""
    for i, row in df.iterrows():
        concept_id = f"concept-{i}"
        items += f"""
        <div class="library-item" onclick="toggleDefinition('{concept_id}')">
          <h3>{row['Concept']}</h3>
          <div id="{concept_id}" class="definition">{row['Definition']}</div>
        </div>
        """
    search_box = """
    <div class="search-box">
      <input type="text" id="searchInput" oninput="filterConcepts()" placeholder="Search concepts...">
    </div>
    """
    return render_template_string(
        BASE_TEMPLATE,
        title="Glossary Library",
        heading="📚 Click a Concept to View the Definition",
        concept=None,
        definition=None,
        extra=search_box + f"<div class='library-list'>{items}</div>"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)