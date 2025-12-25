from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datenbase import get_db            # Deine DB-Verbindung
from repositories import UserRepository # Dein Koch
from schemas import UserResponse, UserCreate     # Dein Sieb
from models import User
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

def get_user_repo(db: Session = Depends(get_db)):
    return UserRepository(db)
# --- USER ENDPUNKTE (Bisheriger Code) ---

@router.get("/", summary="Basis-Status", tags=["Status"]) # / heißt das ist die Startseite (Hauseingang) == Standart Pfad
def read_root():
    return {"message": "Backend läuft. Gehe zu /docs zum Testen der API."}

# GET /users
@router.get("/users", response_model=List[UserResponse], summary="Alle Benutzer abrufen (Filterbar nach Name)", tags=["Benutzer"]) #/useres (Tür zu Users), 
def get_all_users(name: str | None = None, repo: UserRepository = Depends(get_user_repo)):
   
    users = repo.get_all_users(name_filter=name) 
    
    return users

# GET /users/{user_id}
@router.get("/users/{user_id}", response_model = UserResponse, summary="Einzelnen Benutzer abrufen", tags=["Benutzer"]) #response_model=UserResponse muss da sein es sagt das es dem von UserRespone entsprechen muss
#es kommt also ein Objekt raus was genau so aussieht wie UserResponse 
def get_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    user = repo.get_user_by_id(user_id) 
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

# POST /users
@router.post("/users", response_model=UserResponse, summary="Neuen Benutzer erstellen", tags=["Benutzer"])
def create_user(user_data: UserCreate, repo: UserRepository = Depends(get_user_repo)): #die user_datei muss den Typ UserCreate entsprechen weil : UserCreate (Validierung)
   
    new_user_obj = User(name=user_data.name, email=user_data.email)
    
    saved_user = repo.save_user(new_user_obj) #hier wird das user_obj in im UserRepository erstellt und durch das ausgetauscht
    

    if saved_user is None:
        raise HTTPException(status_code=409, detail=f"User with email '{user_data.email}' already exists (Conflict)")
    return saved_user

# PUT /users/{user_id}
@router.put("/users/{user_id}", response_model=UserResponse, summary="Benutzer aktualisieren", tags=["Benutzer"])
def update_user_api(user_id: int, user_data: UserResponse, repo: UserRepository = Depends(get_user_repo)):
   
    user_obj = User(user_id=user_id, name=user_data.name, email=user_data.email)
    updated_user = repo.update_user(user_obj)
    

    if updated_user is None:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found or email conflict.")
            
    return updated_user

# DELETE /users/{user_id}
@router.delete("/users/{user_id}", summary="Benutzer löschen", tags=["Benutzer"]) #packe das in die kategorie tags 
def delete_user_api(user_id: int, repo: UserRepository = Depends(get_user_repo)):
 
    was_deleted = repo.delete_user(user_id)
   

    if not was_deleted:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
    return {"message": f"User with ID {user_id} successfully deleted"}
