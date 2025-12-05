from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from typing import List, Dict

# MESMA URL DO TEU load_f1_data.py
DATABASE_URL = "postgresql+psycopg2://f1user:f1password@localhost:5432/f1db"

engine = create_engine(DATABASE_URL)

app = FastAPI(title="F1 Dashboard API")


# ---------- HELPERS ----------

def query_all_dict(sql: str, params: Dict | None = None) -> List[Dict]:
    """Executa SELECT e retorna lista de dicts."""
    params = params or {}
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        rows = result.mappings().all()
        return [dict(r) for r in rows]


# ---------- ENDPOINTS DE DADOS ----------

@app.get("/api/seasons")
def get_seasons():
    """
    Lista todas as temporadas disponíveis (anos).
    """
    rows = query_all_dict("""
        SELECT DISTINCT year
        FROM seasons
        ORDER BY year DESC
    """)
    return {"seasons": [r["year"] for r in rows]}


@app.get("/api/top-drivers-wins")
def get_top_drivers_wins(limit: int = 10):
    """
    Top pilotos por número total de vitórias (todas as temporadas).
    """
    rows = query_all_dict("""
        SELECT
            d."driverId" AS driver_id,
            d.forename || ' ' || d.surname AS driver_name,
            COUNT(*) AS wins
        FROM results r
        JOIN drivers d ON r."driverId" = d."driverId"
        WHERE r.position = 1
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY wins DESC
        LIMIT :limit
    """, {"limit": limit})

    return {"data": rows}


@app.get("/api/constructors-wins")
def get_constructors_wins(season: int):
    """
    Vitórias por equipe numa temporada específica.
    """
    rows = query_all_dict("""
        SELECT
            c."constructorId" AS constructor_id,
            c.name AS constructor_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN constructors c ON r."constructorId" = c."constructorId"
        WHERE ra.year = :season
          AND r.position = 1
        GROUP BY c."constructorId", c.name
        ORDER BY wins DESC;
    """, {"season": season})

    return {"season": season, "data": rows}


@app.get("/api/driver-standings")
def get_driver_standings(season: int, limit: int = 10):
    """
    Pontuação final dos pilotos na temporada (usa tabela driver_standings).
    """
    rows = query_all_dict("""
        SELECT
            d."driverId" AS driver_id,
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races ra ON ds."raceId" = ra."raceId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE ra.year = :season
          AND ds."raceId" = (
              SELECT MAX("raceId")
              FROM races
              WHERE year = :season
          )
        ORDER BY ds.position
        LIMIT :limit;
    """, {"season": season, "limit": limit})

    return {"season": season, "data": rows}


@app.get("/api/status-distribution")
def get_status_distribution(season: int):
    """
    Distribuição de resultados (Finished, Engine, Accident, etc) numa temporada.
    """
    rows = query_all_dict("""
        SELECT
            s.status,
            COUNT(*) AS count
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN status s ON r."statusId" = s."statusId"
        WHERE ra.year = :season
        GROUP BY s.status
        ORDER BY count DESC;
    """, {"season": season})

    return {"season": season, "data": rows}


# ---------- FRONTEND ESTÁTICO ----------

# Vai servir os arquivos da pasta "frontend" na raiz do site
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
