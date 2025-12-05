from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import csv
import os
from datetime import datetime

# ===================== CONFIGURAÇÕES =====================

# Ajusta para tua URL real do banco PostgreSQL, por exemplo:
# postgresql+psycopg2://usuario:senha@host:porta/nome_banco
DATABASE_URL = "postgresql+psycopg2://f1user:f1password@localhost:5432/f1db"

# Pasta onde estão os .csv (descompacta o ZIP aqui)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "f1")

Base = declarative_base()

# ===================== MODELOS =====================

class Season(Base):
    __tablename__ = "seasons"
    year = Column(Integer, primary_key=True)
    url = Column(String)


class Circuit(Base):
    __tablename__ = "circuits"
    circuitId = Column(Integer, primary_key=True)
    circuitRef = Column(String)
    name = Column(String)
    location = Column(String)
    country = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    alt = Column(Integer)
    url = Column(String)

    races = relationship("Race", back_populates="circuit")


class Constructor(Base):
    __tablename__ = "constructors"
    constructorId = Column(Integer, primary_key=True)
    constructorRef = Column(String)
    name = Column(String)
    nationality = Column(String)
    url = Column(String)


class Driver(Base):
    __tablename__ = "drivers"
    driverId = Column(Integer, primary_key=True)
    driverRef = Column(String)
    number = Column(Integer)
    code = Column(String(3))
    forename = Column(String)
    surname = Column(String)
    dob = Column(Date)
    nationality = Column(String)
    url = Column(String)


class Status(Base):
    __tablename__ = "status"
    statusId = Column(Integer, primary_key=True)
    status = Column(String)


class Race(Base):
    __tablename__ = "races"
    raceId = Column(Integer, primary_key=True)
    year = Column(Integer, ForeignKey("seasons.year"))
    round = Column(Integer)
    circuitId = Column(Integer, ForeignKey("circuits.circuitId"))
    name = Column(String)
    date = Column(Date)
    time = Column(String)
    url = Column(String)
    fp1_date = Column(Date, nullable=True)
    fp1_time = Column(String, nullable=True)
    fp2_date = Column(Date, nullable=True)
    fp2_time = Column(String, nullable=True)
    fp3_date = Column(Date, nullable=True)
    fp3_time = Column(String, nullable=True)
    quali_date = Column(Date, nullable=True)
    quali_time = Column(String, nullable=True)
    sprint_date = Column(Date, nullable=True)
    sprint_time = Column(String, nullable=True)

    circuit = relationship("Circuit", back_populates="races")


class Result(Base):
    __tablename__ = "results"
    resultId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    driverId = Column(Integer, ForeignKey("drivers.driverId"))
    constructorId = Column(Integer, ForeignKey("constructors.constructorId"))
    number = Column(Integer, nullable=True)
    grid = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)
    positionText = Column(String, nullable=True)
    positionOrder = Column(Integer, nullable=True)
    points = Column(Float)
    laps = Column(Integer, nullable=True)
    time = Column(String, nullable=True)
    milliseconds = Column(Integer, nullable=True)
    fastestLap = Column(Integer, nullable=True)
    rank = Column(Integer, nullable=True)
    fastestLapTime = Column(String, nullable=True)
    fastestLapSpeed = Column(Float, nullable=True)
    statusId = Column(Integer, ForeignKey("status.statusId"), nullable=True)


class SprintResult(Base):
    __tablename__ = "sprint_results"
    resultId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    driverId = Column(Integer, ForeignKey("drivers.driverId"))
    constructorId = Column(Integer, ForeignKey("constructors.constructorId"))
    number = Column(Integer, nullable=True)
    grid = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)
    positionText = Column(String, nullable=True)
    positionOrder = Column(Integer, nullable=True)
    points = Column(Float)
    laps = Column(Integer, nullable=True)
    time = Column(String, nullable=True)
    milliseconds = Column(Integer, nullable=True)
    fastestLap = Column(Integer, nullable=True)
    fastestLapTime = Column(String, nullable=True)
    statusId = Column(Integer, ForeignKey("status.statusId"), nullable=True)


class LapTime(Base):
    __tablename__ = "lap_times"
    # não há id próprio no CSV, usamos PK composta
    raceId = Column(Integer, ForeignKey("races.raceId"), primary_key=True)
    driverId = Column(Integer, ForeignKey("drivers.driverId"), primary_key=True)
    lap = Column(Integer, primary_key=True)
    position = Column(Integer, nullable=True)
    time = Column(String, nullable=True)
    milliseconds = Column(Integer, nullable=True)


class PitStop(Base):
    __tablename__ = "pit_stops"
    raceId = Column(Integer, ForeignKey("races.raceId"), primary_key=True)
    driverId = Column(Integer, ForeignKey("drivers.driverId"), primary_key=True)
    stop = Column(Integer, primary_key=True)
    lap = Column(Integer, nullable=True)
    time = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    milliseconds = Column(Integer, nullable=True)


class Qualifying(Base):
    __tablename__ = "qualifying"
    qualifyId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    driverId = Column(Integer, ForeignKey("drivers.driverId"))
    constructorId = Column(Integer, ForeignKey("constructors.constructorId"))
    number = Column(Integer, nullable=True)
    position = Column(Integer, nullable=True)
    q1 = Column(String, nullable=True)
    q2 = Column(String, nullable=True)
    q3 = Column(String, nullable=True)


class ConstructorResult(Base):
    __tablename__ = "constructor_results"
    constructorResultsId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    constructorId = Column(Integer, ForeignKey("constructors.constructorId"))
    points = Column(Float)
    status = Column(String, nullable=True)


class ConstructorStanding(Base):
    __tablename__ = "constructor_standings"
    constructorStandingsId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    constructorId = Column(Integer, ForeignKey("constructors.constructorId"))
    points = Column(Float)
    position = Column(Integer)
    positionText = Column(String)
    wins = Column(Integer)


class DriverStanding(Base):
    __tablename__ = "driver_standings"
    driverStandingsId = Column(Integer, primary_key=True)
    raceId = Column(Integer, ForeignKey("races.raceId"))
    driverId = Column(Integer, ForeignKey("drivers.driverId"))
    points = Column(Float)
    position = Column(Integer)
    positionText = Column(String)
    wins = Column(Integer)


# ===================== HELPERS =====================

def parse_int(value):
    if value in (None, "", "\\N"):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_float(value):
    if value in (None, "", "\\N"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_date(value):
    if value in (None, "", "\\N"):
        return None
    # formatos possíveis: yyyy-mm-dd
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


# ===================== FUNÇÕES DE CARGA =====================

def load_seasons(session):
    for row in load_csv(os.path.join(DATA_DIR, "seasons.csv")):
        obj = Season(
            year=parse_int(row["year"]),
            url=row.get("url"),
        )
        session.merge(obj)


def load_circuits(session):
    for row in load_csv(os.path.join(DATA_DIR, "circuits.csv")):
        obj = Circuit(
            circuitId=parse_int(row["circuitId"]),
            circuitRef=row.get("circuitRef"),
            name=row.get("name"),
            location=row.get("location"),
            country=row.get("country"),
            lat=parse_float(row.get("lat")),
            lng=parse_float(row.get("lng")),
            alt=parse_int(row.get("alt")),
            url=row.get("url"),
        )
        session.merge(obj)


def load_constructors(session):
    for row in load_csv(os.path.join(DATA_DIR, "constructors.csv")):
        obj = Constructor(
            constructorId=parse_int(row["constructorId"]),
            constructorRef=row.get("constructorRef"),
            name=row.get("name"),
            nationality=row.get("nationality"),
            url=row.get("url"),
        )
        session.merge(obj)


def load_drivers(session):
    for row in load_csv(os.path.join(DATA_DIR, "drivers.csv")):
        obj = Driver(
            driverId=parse_int(row["driverId"]),
            driverRef=row.get("driverRef"),
            number=parse_int(row.get("number")),
            code=row.get("code"),
            forename=row.get("forename"),
            surname=row.get("surname"),
            dob=parse_date(row.get("dob")),
            nationality=row.get("nationality"),
            url=row.get("url"),
        )
        session.merge(obj)


def load_status(session):
    for row in load_csv(os.path.join(DATA_DIR, "status.csv")):
        obj = Status(
            statusId=parse_int(row["statusId"]),
            status=row.get("status"),
        )
        session.merge(obj)


def load_races(session):
    for row in load_csv(os.path.join(DATA_DIR, "races.csv")):
        obj = Race(
            raceId=parse_int(row["raceId"]),
            year=parse_int(row.get("year")),
            round=parse_int(row.get("round")),
            circuitId=parse_int(row.get("circuitId")),
            name=row.get("name"),
            date=parse_date(row.get("date")),
            time=row.get("time"),
            url=row.get("url"),
            fp1_date=parse_date(row.get("fp1_date")),
            fp1_time=row.get("fp1_time"),
            fp2_date=parse_date(row.get("fp2_date")),
            fp2_time=row.get("fp2_time"),
            fp3_date=parse_date(row.get("fp3_date")),
            fp3_time=row.get("fp3_time"),
            quali_date=parse_date(row.get("quali_date")),
            quali_time=row.get("quali_time"),
            sprint_date=parse_date(row.get("sprint_date")),
            sprint_time=row.get("sprint_time"),
        )
        session.merge(obj)


def load_results(session):
    for row in load_csv(os.path.join(DATA_DIR, "results.csv")):
        obj = Result(
            resultId=parse_int(row["resultId"]),
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            constructorId=parse_int(row.get("constructorId")),
            number=parse_int(row.get("number")),
            grid=parse_int(row.get("grid")),
            position=parse_int(row.get("position")),
            positionText=row.get("positionText"),
            positionOrder=parse_int(row.get("positionOrder")),
            points=parse_float(row.get("points")),
            laps=parse_int(row.get("laps")),
            time=row.get("time"),
            milliseconds=parse_int(row.get("milliseconds")),
            fastestLap=parse_int(row.get("fastestLap")),
            rank=parse_int(row.get("rank")),
            fastestLapTime=row.get("fastestLapTime"),
            fastestLapSpeed=parse_float(row.get("fastestLapSpeed")),
            statusId=parse_int(row.get("statusId")),
        )
        session.merge(obj)


def load_sprint_results(session):
    for row in load_csv(os.path.join(DATA_DIR, "sprint_results.csv")):
        obj = SprintResult(
            resultId=parse_int(row["resultId"]),
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            constructorId=parse_int(row.get("constructorId")),
            number=parse_int(row.get("number")),
            grid=parse_int(row.get("grid")),
            position=parse_int(row.get("position")),
            positionText=row.get("positionText"),
            positionOrder=parse_int(row.get("positionOrder")),
            points=parse_float(row.get("points")),
            laps=parse_int(row.get("laps")),
            time=row.get("time"),
            milliseconds=parse_int(row.get("milliseconds")),
            fastestLap=parse_int(row.get("fastestLap")),
            fastestLapTime=row.get("fastestLapTime"),
            statusId=parse_int(row.get("statusId")),
        )
        session.merge(obj)


def load_lap_times(session):
    for row in load_csv(os.path.join(DATA_DIR, "lap_times.csv")):
        obj = LapTime(
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            lap=parse_int(row.get("lap")),
            position=parse_int(row.get("position")),
            time=row.get("time"),
            milliseconds=parse_int(row.get("milliseconds")),
        )
        session.merge(obj)


def load_pit_stops(session):
    for row in load_csv(os.path.join(DATA_DIR, "pit_stops.csv")):
        obj = PitStop(
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            stop=parse_int(row.get("stop")),
            lap=parse_int(row.get("lap")),
            time=row.get("time"),
            duration=row.get("duration"),
            milliseconds=parse_int(row.get("milliseconds")),
        )
        session.merge(obj)


def load_qualifying(session):
    for row in load_csv(os.path.join(DATA_DIR, "qualifying.csv")):
        obj = Qualifying(
            qualifyId=parse_int(row.get("qualifyId")),
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            constructorId=parse_int(row.get("constructorId")),
            number=parse_int(row.get("number")),
            position=parse_int(row.get("position")),
            q1=row.get("q1"),
            q2=row.get("q2"),
            q3=row.get("q3"),
        )
        session.merge(obj)


def load_constructor_results(session):
    for row in load_csv(os.path.join(DATA_DIR, "constructor_results.csv")):
        obj = ConstructorResult(
            constructorResultsId=parse_int(row.get("constructorResultsId")),
            raceId=parse_int(row.get("raceId")),
            constructorId=parse_int(row.get("constructorId")),
            points=parse_float(row.get("points")),
            status=row.get("status"),
        )
        session.merge(obj)


def load_constructor_standings(session):
    for row in load_csv(os.path.join(DATA_DIR, "constructor_standings.csv")):
        obj = ConstructorStanding(
            constructorStandingsId=parse_int(row.get("constructorStandingsId")),
            raceId=parse_int(row.get("raceId")),
            constructorId=parse_int(row.get("constructorId")),
            points=parse_float(row.get("points")),
            position=parse_int(row.get("position")),
            positionText=row.get("positionText"),
            wins=parse_int(row.get("wins")),
        )
        session.merge(obj)


def load_driver_standings(session):
    for row in load_csv(os.path.join(DATA_DIR, "driver_standings.csv")):
        obj = DriverStanding(
            driverStandingsId=parse_int(row.get("driverStandingsId")),
            raceId=parse_int(row.get("raceId")),
            driverId=parse_int(row.get("driverId")),
            points=parse_float(row.get("points")),
            position=parse_int(row.get("position")),
            positionText=row.get("positionText"),
            wins=parse_int(row.get("wins")),
        )
        session.merge(obj)


def main():
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Ordem importa por causa das FKs
        load_seasons(session)
        load_circuits(session)
        load_constructors(session)
        load_drivers(session)
        load_status(session)
        load_races(session)
        load_results(session)
        load_sprint_results(session)
        load_lap_times(session)
        load_pit_stops(session)
        load_qualifying(session)
        load_constructor_results(session)
        load_constructor_standings(session)
        load_driver_standings(session)

        session.commit()
        print("Carga concluída com sucesso!")
    except Exception as e:
        session.rollback()
        print("Erro durante a carga:", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
