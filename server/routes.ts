import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import pg from "pg";

const { Pool } = pg;

// Single pool for the whole app; uses the same default as api.py
const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL ??
    "postgresql://f1user:f1password@localhost:5432/f1db",
  // keep defaults for pool size/timeout similar to python config
  max: 15,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 30_000,
});

async function queryAll(sql: string, params: any = {}) {
  const client = await pool.connect();
  try {
    const res = await client.query(sql, params);
    return res.rows;
  } catch (err) {
    // surface a concise error to client
    const error = new Error("Database unavailable");
    // attach status for error middleware
    (error as any).status = 503;
    throw error;
  } finally {
    client.release();
  }
}

function handleError(res: Response, err: any) {
  const status = err?.status ?? 500;
  const message = err?.message ?? "Internal Server Error";
  res.status(status).json({ message });
}

export async function registerRoutes(
  httpServer: Server,
  app: Express,
): Promise<Server> {
  // --- Ping ---
  app.get("/api/ping", (_req, res) => res.json({ status: "ok" }));

  // --- Overview endpoints ---
  app.get("/api/top-drivers-wins", async (req: Request, res: Response) => {
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "10", 10), 1),
      200,
    );
    try {
      const rows = await queryAll(
        `
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            COUNT(*) AS wins
        FROM results r
        JOIN drivers d ON r."driverId" = d."driverId"
        WHERE r.position = 1
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY wins DESC
        LIMIT $1
      `,
        [limit],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/constructors-wins", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "20", 10), 1),
      200,
    );
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    try {
      const rows = await queryAll(
        `
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN constructors c ON r."constructorId" = c."constructorId"
        WHERE ra.year = $1
          AND r.position = 1
        GROUP BY c."constructorId", c.name
        ORDER BY wins DESC
        LIMIT $2
      `,
        [season, limit],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/driver-standings", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "10", 10), 1),
      200,
    );
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    try {
      const rows = await queryAll(
        `
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races ra ON ds."raceId" = ra."raceId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE ra.year = $1
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE r2.year = $1
          )
        ORDER BY ds.position
        LIMIT $2
      `,
        [season, limit],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/status-distribution", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    try {
      const rows = await queryAll(
        `
        SELECT
            s.status,
            COUNT(*) AS count
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN status s ON r."statusId" = s."statusId"
        WHERE ra.year = $1
        GROUP BY s.status
        ORDER BY count DESC
      `,
        [season],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Circuits ---
  app.get("/api/circuits", async (req: Request, res: Response) => {
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "50", 10), 1),
      200,
    );
    const offset = Math.max(parseInt((req.query.offset as string) ?? "0", 10), 0);
    try {
      const rows = await queryAll(
        `
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
        LIMIT $1 OFFSET $2
      `,
        [limit, offset],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/circuits/:id", async (req: Request, res: Response) => {
    const cid = parseInt(req.params.id, 10);
    if (Number.isNaN(cid)) {
      return res.status(400).json({ message: "invalid circuit id" });
    }
    try {
      const info = await queryAll(
        `
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
        WHERE c."circuitId" = $1
        GROUP BY c."circuitId", c.name, c.country, c.location
      `,
        [cid],
      );
      const topDrivers = await queryAll(
        `
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN drivers d ON r."driverId" = d."driverId"
        WHERE ra."circuitId" = $1
          AND r.position = 1
        GROUP BY d."driverId", d.forename, d.surname
        ORDER BY wins DESC
        LIMIT 15
      `,
        [cid],
      );
      const topConstructors = await queryAll(
        `
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            COUNT(*) AS wins
        FROM results r
        JOIN races ra ON r."raceId" = ra."raceId"
        JOIN constructors c ON r."constructorId" = c."constructorId"
        WHERE ra."circuitId" = $1
          AND r.position = 1
        GROUP BY c."constructorId", c.name
        ORDER BY wins DESC
        LIMIT 15
      `,
        [cid],
      );
      res.json({
        info: info[0] ?? null,
        top_drivers: topDrivers,
        top_constructors: topConstructors,
      });
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Constructors ---
  app.get("/api/constructors", async (req: Request, res: Response) => {
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "50", 10), 1),
      200,
    );
    const offset = Math.max(parseInt((req.query.offset as string) ?? "0", 10), 0);
    try {
      const rows = await queryAll(
        `
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
        LIMIT $1 OFFSET $2
      `,
        [limit, offset],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/constructors/:id", async (req: Request, res: Response) => {
    const cid = parseInt(req.params.id, 10);
    if (Number.isNaN(cid)) {
      return res.status(400).json({ message: "invalid constructor id" });
    }
    try {
      const info = await queryAll(
        `
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
        WHERE c."constructorId" = $1
        GROUP BY c."constructorId", c.name, c.nationality
      `,
        [cid],
      );
      const winsByYear = await queryAll(
        `
        SELECT
            r.year,
            COUNT(*) FILTER (WHERE res.position = 1) AS wins,
            COUNT(*) AS races
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE res."constructorId" = $1
        GROUP BY r.year
        HAVING COUNT(*) > 0
        ORDER BY r.year
      `,
        [cid],
      );
      res.json({
        info: info[0] ?? null,
        years: winsByYear,
      });
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Drivers ---
  app.get("/api/drivers", async (req: Request, res: Response) => {
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "50", 10), 1),
      200,
    );
    const offset = Math.max(parseInt((req.query.offset as string) ?? "0", 10), 0);
    try {
      const rows = await queryAll(
        `
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
        LIMIT $1 OFFSET $2
      `,
        [limit, offset],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/drivers/:id", async (req: Request, res: Response) => {
    const did = parseInt(req.params.id, 10);
    if (Number.isNaN(did)) {
      return res.status(400).json({ message: "invalid driver id" });
    }
    try {
      const info = await queryAll(
        `
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
        WHERE d."driverId" = $1
        GROUP BY d."driverId", d.forename, d.surname, d.nationality, d.dob
      `,
        [did],
      );
      const history = await queryAll(
        `
        SELECT
            r.year,
            r.round,
            r.name AS grand_prix,
            res.points,
            res.position
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE res."driverId" = $1
        ORDER BY r.year, r.round
      `,
        [did],
      );
      const seasons = await queryAll(
        `
        SELECT
            r.year,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races r ON ds."raceId" = r."raceId"
        WHERE ds."driverId" = $1
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE ds2."driverId" = $1
                AND r2.year = r.year
          )
        ORDER BY r.year
      `,
        [did],
      );
      res.json({
        info: info[0] ?? null,
        history,
        seasons,
      });
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Seasons ---
  app.get("/api/seasons", async (_req: Request, res: Response) => {
    try {
      const rows = await queryAll(
        `
        SELECT DISTINCT year
        FROM races
        ORDER BY year DESC
      `,
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  app.get("/api/seasons/:year/winners", async (req: Request, res: Response) => {
    const year = parseInt(req.params.year, 10);
    if (Number.isNaN(year)) {
      return res.status(400).json({ message: "invalid year" });
    }
    try {
      const races = await queryAll(
        `
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
        WHERE r.year = $1
          AND res.position = 1
        ORDER BY r.round
      `,
        [year],
      );
      const driverChampion = await queryAll(
        `
        SELECT
            d."driverId" AS "driverId",
            d.forename || ' ' || d.surname AS driver_name,
            ds.points,
            ds.position
        FROM driver_standings ds
        JOIN races r ON ds."raceId" = r."raceId"
        JOIN drivers d ON ds."driverId" = d."driverId"
        WHERE r.year = $1
          AND ds."raceId" = (
              SELECT MAX(ds2."raceId")
              FROM driver_standings ds2
              JOIN races r2 ON ds2."raceId" = r2."raceId"
              WHERE r2.year = $1
          )
          AND ds.position = 1
      `,
        [year],
      );
      const constructorChampion = await queryAll(
        `
        SELECT
            c."constructorId" AS "constructorId",
            c.name AS constructor_name,
            cs.points,
            cs.position
        FROM constructor_standings cs
        JOIN races r ON cs."raceId" = r."raceId"
        JOIN constructors c ON cs."constructorId" = c."constructorId"
        WHERE r.year = $1
          AND cs."raceId" = (
              SELECT MAX(cs2."raceId")
              FROM constructor_standings cs2
              JOIN races r2 ON cs2."raceId" = r2."raceId"
              WHERE r2.year = $1
          )
          AND cs.position = 1
      `,
        [year],
      );
      res.json({
        races,
        driver_champion: driverChampion[0] ?? null,
        constructor_champion: constructorChampion[0] ?? null,
      });
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Pit stops summary ---
  app.get("/api/pit-stops/summary", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    const raceId = req.query.race_id ? parseInt(req.query.race_id as string, 10) : null;
    const groupBy =
      (req.query.group_by as string)?.match(/^(driver|constructor)$/)?.[0] ??
      "driver";
    const limit = Math.min(
      Math.max(parseInt((req.query.limit as string) ?? "30", 10), 1),
      200,
    );
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    const raceFilter = raceId ? `AND r."raceId" = $2` : "";
    const params = raceId ? [season, raceId, limit] : [season, limit];
    const groupFields =
      groupBy === "driver"
        ? `d."driverId" AS "driverId", d.forename || ' ' || d.surname AS label`
        : `c."constructorId" AS "constructorId", c.name AS label`;
    const groupCols =
      groupBy === "driver"
        ? `d."driverId", d.forename, d.surname`
        : `c."constructorId", c.name`;
    try {
      const rows = await queryAll(
        `
        SELECT
            ${groupFields},
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
        WHERE r.year = $1
          ${raceFilter}
          AND ps.milliseconds IS NOT NULL
        GROUP BY ${groupCols}
        ORDER BY pit_stops DESC
        LIMIT $${raceId ? 3 : 2}
      `,
        params,
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Positions heatmap ---
  app.get("/api/positions/heatmap", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    const raceId = req.query.race_id ? parseInt(req.query.race_id as string, 10) : null;
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    const raceFilter = raceId ? `AND r."raceId" = $2` : "";
    const params = raceId ? [season, raceId] : [season];
    try {
      const rows = await queryAll(
        `
        SELECT
            res.grid AS start_position,
            res.position AS finish_position,
            COUNT(*) AS count
        FROM results res
        JOIN races r ON res."raceId" = r."raceId"
        WHERE r.year = $1
          ${raceFilter}
          AND res.grid IS NOT NULL
          AND res.position IS NOT NULL
        GROUP BY res.grid, res.position
        ORDER BY res.grid, res.position
      `,
        params,
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Lap times stats ---
  app.get("/api/lap-times/stats", async (req: Request, res: Response) => {
    const raceId = parseInt(req.query.race_id as string, 10);
    const driverId = req.query.driver_id
      ? parseInt(req.query.driver_id as string, 10)
      : null;
    const topN = Math.min(
      Math.max(parseInt((req.query.top_n as string) ?? "10", 10), 1),
      200,
    );
    if (Number.isNaN(raceId)) {
      return res.status(400).json({ message: "race_id is required" });
    }
    const driverFilter = driverId ? `AND lt."driverId" = $2` : "";
    const params = driverId ? [raceId, driverId, topN] : [raceId, topN];
    try {
      const rows = await queryAll(
        `
        WITH base AS (
            SELECT lt."driverId", lt.milliseconds
            FROM lap_times lt
            WHERE lt."raceId" = $1
              ${driverFilter}
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
        LIMIT $${driverId ? 3 : 2}
      `,
        params,
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  // --- Driver progress ---
  app.get("/api/driver-progress", async (req: Request, res: Response) => {
    const season = parseInt(req.query.season as string, 10);
    const topN = Math.min(
      Math.max(parseInt((req.query.top_n as string) ?? "5", 10), 1),
      200,
    );
    if (Number.isNaN(season)) {
      return res.status(400).json({ message: "season is required" });
    }
    try {
      const rows = await queryAll(
        `
        WITH last_race AS (
            SELECT MAX(r."raceId") AS race_id
            FROM races r
            WHERE r.year = $1
        ),
        top_drivers AS (
            SELECT ds."driverId"
            FROM driver_standings ds
            JOIN last_race lr ON ds."raceId" = lr.race_id
            ORDER BY ds.position
            LIMIT $2
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
        WHERE r.year = $1
        ORDER BY d."driverId", r.round
      `,
        [season, topN],
      );
      res.json(rows);
    } catch (err) {
      handleError(res, err);
    }
  });

  return httpServer;
}
