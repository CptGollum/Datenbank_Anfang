from fastapi import FastAPI
import models
from datenbase import engine, Base
import routers.users as users
import routers.posts as posts

# 1. Tabellen in der DB erstellen
Base.metadata.create_all(bind=engine)

# 2. Die App Instanz
app = FastAPI(title="Mein modulares Programm")
import schemas
print("In schemas gefunden:", dir(schemas))
# 3. Die Router einbinden
app.include_router(users.router)
app.include_router(posts.router)


# Optional: Der Global Exception Handler (den wir aus dem Router entfernt haben)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"KRITISCHER FEHLER: {exc}")
    return {"message": "Fehler im System!"}