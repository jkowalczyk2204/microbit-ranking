import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.on_event("startup")
def startup():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    player_id TEXT NOT NULL,
                    score INT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

class ScoreIn(BaseModel):
    player_id: str
    score: int

@app.post("/api/scores")
def add_score(data: ScoreIn):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO scores (player_id, score) VALUES (%s, %s)", (data.player_id, data.score))
    return {"status": "ok"}

@app.get("/api/leaderboard")
def get_leaderboard(limit: int = 10):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT player_id, score FROM scores ORDER BY score DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            return [{"player_id": r[0], "score": r[1]} for r in rows]

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
      <meta charset="UTF-8">
      <title>Ranking Gry</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-white flex flex-col items-center p-8">
      <h1 class="text-3xl font-bold mb-6 text-emerald-400">Tabela Wyników na Żywo</h1>
      <ol id="tabela" class="w-full max-w-md bg-slate-800 rounded-lg p-4 divide-y divide-slate-700"></ol>
      <script>
        async function odswiez() {
          try {
            const res = await fetch('/api/leaderboard');
            const data = await res.json();
            document.getElementById('tabela').innerHTML = data.map((item, i) => `
              <li class="py-2 flex justify-between">
                <span>${i + 1}. <b>${item.player_id}</b></span>
                <span class="text-emerald-400 font-mono font-bold">${item.score} pkt</span>
              </li>
            `).join('');
          } catch (e) {
            console.error(e);
          }
        }
        odswiez();
        setInterval(odswiez, 3000);
      </script>
    </body>
    </html>
    """
