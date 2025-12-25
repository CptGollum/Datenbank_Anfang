from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List # Wichtig für Listen-Rückgaben
from fastapi.responses import JSONResponse

# Eigene Imports
from datenbase import get_db
from repositories import UserRepository, PostRepository # Beide importieren!
from schemas import PostResponse, PostCreate             # Deine Siebe
from models import Post                                  # Deine Logik-Klasse

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)
def get_post_repo(db: Session = Depends(get_db)):
    return PostRepository(db)

def get_user_repo(db: Session = Depends(get_db)):
    return UserRepository(db)

# --- POST ENDPUNKTE (GANZ NEU: Post-CRUD) ---

# POST /posts
@router.post("/posts", response_model=PostResponse, summary="Neuen Beitrag erstellen", tags=["Beiträge"]) # Response_model bleibt gleich es ist wichtig damit die api später ein Json format sendet
def create_post(post_data: PostCreate, 
                post_repo: PostRepository = Depends(get_post_repo),
                user_repo: UserRepository = Depends(get_user_repo)): # Zweites Repo dazu!
    
    # Check: Gibt es den User?
    user = user_repo.get_user_by_id(post_data.user_id)
    if not user:
        raise HTTPException(
            status_code=404, 
            detail=f"Abbruch: User mit ID {post_data.user_id} existiert nicht. Ein Geist kann keine Posts schreiben!"
        )
    
    post_obj = Post(title=post_data.title, content=post_data.content, user_id=post_data.user_id)
    return post_repo.save_post(post_obj)

# GET /posts/{post_id}
@router.get("/posts/{post_id}", response_model=PostResponse, summary="Einzelnen Beitrag abrufen", tags=["Beiträge"])
def get_post(post_id: int, repo: PostRepository = Depends(get_post_repo)):
   
    post = repo.get_post_by_id(post_id)
    

    if post is None:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")

    return post
    
# GET /users/{user_id}/posts (Alle Posts eines Autors) #das users ist das Objekt und die user_id wo gesucht werden soll = Hauptressource
@router.get("/users/{user_id}/posts", response_model=List[PostResponse], summary="Alle Beiträge eines Benutzers abrufen", tags=["Beiträge"])
def get_user_posts(user_id: int, user_repo: UserRepository = Depends(get_user_repo), post_repo: PostRepository = Depends(get_post_repo)):
    # ----------------------------------------------------
    # 1. PRÜFUNG: Existiert die Hauptressource (User)?
    # ----------------------------------------------------
    
    user_exists = user_repo.get_user_by_id(user_id)
    

    if user_exists is None:
        # User existiert NICHT -> 404 Not Found! (Architektonisch korrekt)
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")

    # ----------------------------------------------------
    # 2. ABFRAGE: Nur wenn User existiert, Posts holen
    # ----------------------------------------------------
    
    posts = post_repo.get_posts_by_user_id(user_id)
    
    
    # ----------------------------------------------------
    # 3. RÜCKGABE: User existiert, Posts sind hier (können leer sein: 200 OK)
    # ----------------------------------------------------
    return posts

# PUT /posts/{post_id}
@router.put("/posts/{post_id}", response_model=PostResponse, summary="Beitrag aktualisieren", tags=["Beiträge"])
def update_post_api(post_id: int, post_data: PostResponse, repo: PostRepository = Depends(get_post_repo)):
    post_obj = Post(
        title=post_data.title, content=post_data.content, user_id=post_data.user_id, post_id=post_id
    )

    
    updated_post = repo.update_post(post_obj)
   

    if updated_post is None:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")

    return updated_post #Fast api wandelt das automatisch in PostResponse um 

# DELETE /posts/{post_id}
@router.delete("/posts/{post_id}", status_code=204, summary="Beitrag löschen", tags=["Beiträge"])
def delete_post_api(post_id: int, repo: PostRepository = Depends(get_post_repo)):
   
    was_deleted = repo.delete_post(post_id)


    if not was_deleted:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")
        
    return was_deleted  

