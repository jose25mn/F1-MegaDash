# api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://f1user:f1password@localhost:5432/f1db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

app = FastAPI(title="F1 Mega Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DEFAULT_LIMIT = 50
MAX_LIMIT = 200
MIN_SEASON = 1950
MAX_SEASON = 2100


def query_all_dict(sql: str, params: dict | None = None):
    """
    Executes a SQL query and returns rows as list[dict], mapping SQLAlchemy errors
    to HTTP 503 with a clean message.
    """
    params = params or {}
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            cols = result.keys()
            return [dict(zip(cols, row)) for row in result]
    except SQLAlchemyError as exc:
        # Log the original error server-side; keep client message concise
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@app.get("/api/ping")
def ping():
    return {"status": "ok"}


# =========================
# 1) OVERVIEW ENDPOINTS
# =========================

@app.get("/api/top-drivers-wins")
def get_top_drivers_wins(
    limit: int = Query(10, ge=1, le=MAX_LIMIT),
):
    rows = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            COUNT(*) AS wins
        FROM results r
        JOIN drivers d ON r."driverId" = d."driverId"
        WHERE r.position = 1
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY wins DESC
        LIMIT :limit
    """, {"limit": limit})
    return rows


@app.get("/api/constructors-wins")
def get_constructors_wins(
    season: int = Query(..., description="Ano da temporada", ge=MIN_SEASON, le=MAX_SEASON),
    limit: int = Query(20, ge=1, le=MAX_LIMIT),
):
    rows = query_all_dict("""
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN constructors c ON r."constructorId" = c."constructorId"
        WHERE ra.year = :season
          AND r.position = 1
        GROUP BY c."constructorId", c.name
        ORDER BY wins DESC
        LIMIT :limit;
    """, {"season": season, "limit": limit})
    return rows


@app.get("/api/driver-standings")
def get_driver_standings(
    season: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON),
    limit: int = Query(10, ge=1, le=MAX_LIMIT),
):
    rows = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races ra ON ds."raceId" = ra."raceId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE ra.year = :season
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE r2.year = :season
          )
        ORDER BY ds.position
        LIMIT :limit;
    """, {"season": season, "limit": limit})
    return rows


@app.get("/api/status-distribution")
def get_status_distribution(season: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON)):
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
    return rows


# =========================
# 2) CIRCUITOS
# =========================

@app.get("/api/circuits")
def list_circuits(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    """
    Lista circuitos com número de GPs realizados.
    """
    rows = query_all_dict("""
        SELECT
            c."circuitId" AS "circuitId",
            c.name,
            c.country,
            c.location,
            COUNT(r."raceId") AS total_races
        FROM circuits c
        LEFT JOIN races r ON r."circuitId" = c."circuitId"
        GROUP BY c."circuitId", c.name, c.country, c.location
        ORDER BY c.name
        LIMIT :limit OFFSET :offset;
    """, {"limit": limit, "offset": offset})
    return rows


@app.get("/api/circuits/{circuit_id}")
def circuit_details(circuit_id: int):
    """
    Detalhes de um circuito + top pilotos/equipes vencedores.
    """
    info = query_all_dict("""
        SELECT
            c."circuitId" AS "circuitId",
            c.name,
            c.country,
            c.location,
            COUNT(r."raceId") AS total_races,
            MIN(r.year) AS first_year,
            MAX(r.year) AS last_year
        FROM circuits c
        LEFT JOIN races r ON r."circuitId" = c."circuitId"
        WHERE c."circuitId" = :cid
        GROUP BY c."circuitId", c.name, c.country, c.location;
    """, {"cid": circuit_id})

    top_drivers = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN drivers d ON r."driverId" = d."driverId"
        WHERE ra."circuitId" = :cid
          AND r.position = 1
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY wins DESC
        LIMIT 15;
    """, {"cid": circuit_id})

    top_constructors = query_all_dict("""
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN constructors c ON r."constructorId" = c."constructorId"
        WHERE ra."circuitId" = :cid
          AND r.position = 1
        GROUP BY c."constructorId", c.name
        ORDER BY wins DESC
        LIMIT 15;
    """, {"cid": circuit_id})

    return {
        "info": info[0] if info else None,
        "top_drivers": top_drivers,
        "top_constructors": top_constructors,
    }


# =========================
# 3) EQUIPES (CONSTRUCTORS)
# =========================

@app.get("/api/constructors")
def list_constructors(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    """
    Lista equipes com corridas, pontos e vitórias totais.
    """
    rows = query_all_dict("""
        SELECT
            c."constructorId" AS "constructorId",
            c.name,
            c.nationality,
            COUNT(DISTINCT r."raceId") AS races,
            COALESCE(SUM(cs.points), 0) AS points,
            COALESCE(SUM(cs.wins), 0) AS wins
        FROM constructors c
        LEFT JOIN constructor_standings cs ON cs."constructorId" = c."constructorId"
        LEFT JOIN races r ON cs."raceId" = r."raceId"
        GROUP BY c."constructorId", c.name, c.nationality
        ORDER BY wins DESC, points DESC
        LIMIT :limit OFFSET :offset;
    """, {"limit": limit, "offset": offset})
    return rows


@app.get("/api/constructors/{constructor_id}")
def constructor_stats(constructor_id: int):
    """
    Detalhes de uma equipe + vitórias por ano.
    """
    info = query_all_dict("""
        SELECT
            c."constructorId" AS "constructorId",
            c.name,
            c.nationality,
            COUNT(DISTINCT r."raceId") AS races,
            COALESCE(SUM(cs.points), 0) AS points,
            COALESCE(SUM(cs.wins), 0) AS wins
        FROM constructors c
        LEFT JOIN constructor_standings cs ON cs."constructorId" = c."constructorId"
        LEFT JOIN races r ON cs."raceId" = r."raceId"
        WHERE c."constructorId" = :cid
        GROUP BY c."constructorId", c.name, c.nationality;
    """, {"cid": constructor_id})

    wins_by_year = query_all_dict("""
        SELECT
            r.year,
            COUNT(*) FILTER (WHERE res.position = 1) AS wins,
            COUNT(*) AS races
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE res."constructorId" = :cid
        GROUP BY r.year
        HAVING COUNT(*) > 0
        ORDER BY r.year;
    """, {"cid": constructor_id})

    return {
        "info": info[0] if info else None,
        "years": wins_by_year,
    }


# =========================
# 4) PILOTOS
# =========================

@app.get("/api/drivers")
def list_drivers(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    """
    Lista pilotos com estatísticas básicas.
    """
    rows = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename,
            d.surname,
            d.nationality,
            COUNT(DISTINCT r."raceId") AS races,
            COALESCE(SUM(CASE WHEN res.position = 1 THEN 1 ELSE 0 END), 0) AS wins,
            COALESCE(SUM(CASE WHEN res.position <= 3 AND res.position IS NOT NULL THEN 1 ELSE 0 END), 0) AS podiums
        FROM drivers d
        LEFT JOIN results res ON res."driverId" = d."driverId"
        LEFT JOIN races r ON res."raceId" = r."raceId"
        GROUP BY d."driverId", d.forename, d.surname, d.nationality
        HAVING COUNT(DISTINCT r."raceId") > 0
        ORDER BY wins DESC, podiums DESC
        LIMIT :limit OFFSET :offset;
    """, {"limit": limit, "offset": offset})
    return rows


@app.get("/api/drivers/{driver_id}")
def driver_profile(driver_id: int):
    """
    Perfil do piloto: histórico de corridas + posição por temporada.
    """
    info = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename,
            d.surname,
            d.nationality,
            d.dob,
            COUNT(DISTINCT r."raceId") AS races,
            COALESCE(SUM(CASE WHEN res.position = 1 THEN 1 ELSE 0 END), 0) AS wins,
            COALESCE(SUM(CASE WHEN res.position <= 3 AND res.position IS NOT NULL THEN 1 ELSE 0 END), 0) AS podiums
        FROM drivers d
        LEFT JOIN results res ON res."driverId" = d."driverId"
        LEFT JOIN races r ON res."raceId" = r."raceId"
        WHERE d."driverId" = :did
        GROUP BY d."driverId", d.forename, d.surname, d.nationality, d.dob;
    """, {"did": driver_id})

    history = query_all_dict("""
        SELECT
            r.year,
            r.round,
            r.name AS grand_prix,
            res.points,
            res.position
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE res."driverId" = :did
        ORDER BY r.year, r.round;
    """, {"did": driver_id})

    seasons = query_all_dict("""
        SELECT
            r.year,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races r ON ds."raceId" = r."raceId"
        WHERE ds."driverId" = :did
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE ds2."driverId" = :did
                AND r2.year = r.year
          )
        ORDER BY r.year;
    """, {"did": driver_id})

    return {
        "info": info[0] if info else None,
        "history": history,
        "seasons": seasons,
    }


# =========================
# 5) TEMPORADAS
# =========================

@app.get("/api/seasons")
def list_seasons():
    """
    Lista anos disponíveis.
    """
    rows = query_all_dict("""
        SELECT DISTINCT year
        FROM races
        ORDER BY year DESC;
    """)
    return rows


@app.get("/api/seasons/{year}/winners")
def season_winners(year: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON)):
    """
    Lista corridas da temporada + vencedores.
    """
    races = query_all_dict("""
        SELECT
            r."raceId" AS "raceId",
            r.round,
            r.name AS grand_prix,
            d.forename || ' ' || d.surname AS winner,
            c.name AS constructor,
            res.points
        FROM races r
        JOIN results res ON res."raceId" = r."raceId"
        JOIN drivers d ON res."driverId" = d."driverId"
        JOIN constructors c ON res."constructorId" = c."constructorId"
        WHERE r.year = :year
          AND res.position = 1
        ORDER BY r.round;
    """, {"year": year})

    # campeão de pilotos
    champion_driver = query_all_dict("""
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races r ON ds."raceId" = r."raceId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE r.year = :year
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE r2.year = :year
          )
          AND ds.position = 1;
    """, {"year": year})

    # campeão de construtores
    champion_constructor = query_all_dict("""
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            cs.points,
            cs.position
        FROM constructor_standings cs
        JOIN races r ON cs."raceId" = r."raceId"
        JOIN constructors c ON cs."constructorId" = c."constructorId"
        WHERE r.year = :year
          AND cs."raceId" = (
              SELECT MAX(cs2."raceId")
              FROM constructor_standings cs2
              JOIN races r2 ON cs2."raceId" = r2."raceId"
              WHERE r2.year = :year
          )
          AND cs.position = 1;
    """, {"year": year})

    return {
        "races": races,
        "driver_champion": champion_driver[0] if champion_driver else None,
        "constructor_champion": champion_constructor[0] if champion_constructor else None,
    }


# =========================
# 6) ANALÍTICAS AVANÇADAS
# =========================


@app.get("/api/pit-stops/summary")
def pit_stop_summary(
    season: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON),
    race_id: int | None = Query(None, ge=1),
    group_by: str = Query("driver", pattern="^(driver|constructor)$"),
    limit: int = Query(30, ge=1, le=MAX_LIMIT),
):
    """
    Resumo de pit stops por piloto ou equipe em uma temporada (opcional por corrida).
    Retorna contagem e estatísticas p50/p95 da duração (ms).
    """
    race_filter = "AND r.\"raceId\" = :race_id" if race_id else ""
    group_fields = """
        d."driverId" AS "driverId",
        d.forename || ' ' || d.surname AS label
    """ if group_by == "driver" else """
        c."constructorId" AS "constructorId",
        c.name AS label
    """
    group_cols = "d.\"driverId\", d.forename, d.surname" if group_by == "driver" else "c.\"constructorId\", c.name"

    rows = query_all_dict(f"""
        SELECT
            {group_fields},
            COUNT(*) AS pit_stops,
            AVG(ps.milliseconds) AS avg_ms,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.milliseconds) AS p50_ms,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY ps.milliseconds) AS p95_ms,
            MIN(ps.milliseconds) AS min_ms,
            MAX(ps.milliseconds) AS max_ms
        FROM pit_stops ps
        JOIN races r ON ps."raceId" = r."raceId"
        JOIN results res ON res."raceId" = ps."raceId" AND res."driverId" = ps."driverId"
        JOIN drivers d ON d."driverId" = ps."driverId"
        JOIN constructors c ON c."constructorId" = res."constructorId"
        WHERE r.year = :season
          {race_filter}
          AND ps.milliseconds IS NOT NULL
        GROUP BY {group_cols}
        ORDER BY pit_stops DESC
        LIMIT :limit;
    """, {"season": season, "race_id": race_id, "limit": limit})
    return rows


@app.get("/api/positions/heatmap")
def position_heatmap(
    season: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON),
    race_id: int | None = Query(None, ge=1),
):
    """
    Heatmap de posições: grid (largada) vs posição final.
    """
    race_filter = "AND r.\"raceId\" = :race_id" if race_id else ""
    rows = query_all_dict(f"""
        SELECT
            res.grid AS start_position,
            res.position AS finish_position,
            COUNT(*) AS count
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE r.year = :season
          {race_filter}
          AND res.grid IS NOT NULL
          AND res.position IS NOT NULL
        GROUP BY res.grid, res.position
        ORDER BY res.grid, res.position;
    """, {"season": season, "race_id": race_id})
    return rows


@app.get("/api/lap-times/stats")
def lap_time_stats(
    race_id: int = Query(..., ge=1, description="ID da corrida (obrigatório)"),
    driver_id: int | None = Query(None, ge=1),
    top_n: int = Query(10, ge=1, le=MAX_LIMIT),
):
    """
    Estatísticas de tempos de volta para uma corrida: p50/p95/best por piloto.
    """
    driver_filter = "AND lt.\"driverId\" = :driver_id" if driver_id else ""
    rows = query_all_dict(f"""
        WITH base AS (
            SELECT lt."driverId", lt.milliseconds
            FROM lap_times lt
            WHERE lt."raceId" = :race_id
              {driver_filter}
              AND lt.milliseconds IS NOT NULL
        )
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY base.milliseconds) AS p50_ms,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY base.milliseconds) AS p95_ms,
            MIN(base.milliseconds) AS best_ms,
            MAX(base.milliseconds) AS worst_ms,
            COUNT(*) AS laps
        FROM base
        JOIN drivers d ON base."driverId" = d."driverId"
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY p50_ms ASC
        LIMIT :top_n;
    """, {"race_id": race_id, "driver_id": driver_id, "top_n": top_n})
    return rows


@app.get("/api/driver-progress")
def driver_progress(
    season: int = Query(..., ge=MIN_SEASON, le=MAX_SEASON),
    top_n: int = Query(5, ge=1, le=MAX_LIMIT),
):
    """
    Evolução de pontos por corrida para os top N pilotos da temporada.
    """
    rows = query_all_dict("""
        WITH last_race AS (
            SELECT MAX(r."raceId") AS race_id
            FROM races r
            WHERE r.year = :season
        ),
        top_drivers AS (
            SELECT ds."driverId"
            FROM driver_standings ds
            JOIN last_race lr ON ds."raceId" = lr.race_id
            ORDER BY ds.position
            LIMIT :top_n
        )
        SELECT
            r.round,
            r.name AS grand_prix,
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races r ON ds."raceId" = r."raceId"
        JOIN top_drivers td ON ds."driverId" = td."driverId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE r.year = :season
        ORDER BY d."driverId", r.round;
    """, {"season": season, "top_n": top_n})
    return rows
