from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./userdaten.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) #die engine ist der Motor ohne sie gibt es keine Verbindung zur Db und auch nur sie kann mit ihr kommunizieren und weiß wo sie ist
#das connect_args ist ein spezifischer Befehl für sql das einzelnde threads auch gleichseitig laufen dürfen  
   
Base = declarative_base() #ist eine Kopie vom Regelbuch von SQL / später weiß sql das es die Python befehle übersetzen muss in SQL
SessionLocal = sessionmaker(bind=engine) #wir binden die engine an um immer wenn wir was in der db ändern wollen eine direkte verbindung zur db zu haben,
#zusätzlich ist das von relevanz weil wir mit sessionmaker verschiedene sachen in der db ändern können wie add etc und um diese änderung zu bewergställigen brauchen wir eine db verbindung also (bind = engine)

#Datenbank-Dependency
#damit wenn ein Fehler bei .close() ist sich das trotzdem schließt damit die db nicht unnötig laggt und daten verbraucht
# Eine Funktion, die ein Repository bereitstellt
#Dependency Injection (Abhängigkeits-Injektion)
def get_db(): #dient dazu wenn man mehrere anbindungen hat die gleichseitig eine eigene session haben wollen hiermit nehmen beide die gleiche
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()