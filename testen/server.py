from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# SQLAlchemy Importe für die Datenbank und Beziehungen (WICHTIG: ForeignKey und relationship)
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
# FÜGE DIESE ZEILE in deiner models/XXX_model.py HINZU
from sqlalchemy.orm import Mapped, mapped_column, relationship,sessionmaker, joinedload, Session
# Beachte: Die Klasse 'relationship' brauchst du auch für Mapped[List[...]]
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# ----------------------------------------------------
# 1. DATENBANK KONFIGURATION & MODELLE
# ----------------------------------------------------

DATABASE_URL = "sqlite:///./userdaten.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) #die engine ist der Motor ohne sie gibt es keine Verbindung zur Db und auch nur sie kann mit ihr kommunizieren und weiß wo sie ist
#das connect_args ist ein spezifischer Befehl für sql das einzelnde threads auch gleichseitig laufen dürfen  
   
Base = declarative_base() #ist eine Kopie vom Regelbuch von SQL / später weiß sql das es die Python befehle übersetzen muss in SQL
SessionLocal = sessionmaker(bind=engine) #wir binden die engine an um immer wenn wir was in der db ändern wollen eine direkte verbindung zur db zu haben,
#zusätzlich ist das von relevanz weil wir mit sessionmaker verschiedene sachen in der db ändern können wie add etc und um diese änderung zu bewergställigen brauchen wir eine db verbindung also (bind = engine)

# 🟦 DATENBANK-MODELL: User (ERWEITERT UM DIE BEZIEHUNG)
class UserModel(Base): #bekommt Base vererbt und ist somit eine Tochterklasse = User_Model bekommt alle Fähigkeiten von Base
    __tablename__ = 'users' #durch base in User_Model weiß Sql das es eine tabelle in der db mit namen users anlegen muss
    id : Mapped[int] = mapped_column(Integer, primary_key=True)# primary_key macht das die id unique ist, gleichermaßen zählt sie auch automatisch nach oben
    name: Mapped[str] = mapped_column(String)
    email : Mapped[str] = mapped_column(String, unique=True) #emails sind einzigartig
    
    # 🔗 NEUE ZEILE: Beziehung zu Posts (Ein User hat viele Posts)
    # In models/user_model.py

    """
    also diese mapped dient als synchronisation von python und der db, denn python kennt nur pythonobjekte wie int etc, und die db nur columns etc,
    es synchronisiert also die python welt mit der db welt
    """
    posts: Mapped[List["PostModel"]] = relationship(
        back_populates="author",
        # Hier definieren wir das kaskadierende Verhalten für SQLAlchemy
        cascade="all, delete-orphan" #cascade sorgt dafür das alle posts gelöscht werden wenn auch der user dafür gelöscht wird
    )

# 🟦 DATENBANK-MODELL: Post (GANZ NEU) ist das gleiche wie bei User_Model
class PostModel(Base):
    __tablename__ = 'posts'

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    
    # 🔗 FREMDSCHLÜSSEL: Verweist auf die users.id (DIE VERBINDUNG)
    # In models/post_model.py
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))#das ist für die Datenbank
    
    # 🔗 Beziehung: Ein Post gehört zu einem User
    author: Mapped["UserModel"] = relationship(back_populates="posts") # das : Mapped[] sagt es wird später ein objekt von UserModel sein   
# Erstellt die Tabellen (Users und Posts)
Base.metadata.create_all(engine) #die Klassen welche Base vererbt bekommen haben sind zwar Baupläne aber die Tabelle die sie erstellen wollen,
# gibt es noch nicht als Tabelle in der db sondern nur als Bauplan in der metadata im Ram meines Pcs, um diese Tabelle in die db zu schreiben muss man,
# diesen Befehl Base.metadata.create_all(engine) machen sonnst wird keine Tabelle in der db erstellt

# ----------------------------------------------------
# 2. LOGIK KLASSEN (Domain-Objekte)
# ----------------------------------------------------
#sie sind die Objekt welche weniger datenballast mit sich tragen flexibler sind als z.b UserModel 
#sie werden verwendet um sachen umzuschreiben uns später werden sie wieder in UserModel umgewandelt und abgespeichert

class User:
    def __init__(self, name: str, email: str, user_id: int = None): #self weil wir die Werte anpassen wollen und int = None weil wir hier noch nicht bestimmen wollen was die id ist
        self.id = user_id
        self.name = name
        self.email = email 

class Post: # NEU
    def __init__(self, title: str, content: str, user_id: int, post_id: int = None):
        self.id = post_id
        self.title = title
        self.content = content
        self.user_id = user_id

# ----------------------------------------------------
# 3. REPOSITORIES (Küchenchefs)
# ----------------------------------------------------

# REPOSITORY FÜR USER (Hier nur gekürzt, ist in deinem Code enthalten)
class UserRepository:
    def __init__(self, db_session: Session):
        self.session = db_session

    def close(self):
        self.session.close()

    # CRUD: CREATE (POST)
    def save_user(self, user_obj: User): # Das ": User" ist der Hinweis, user_obj ist nur ein Platzhalter 
        try:
            db_model = UserModel(name=user_obj.name, email=user_obj.email)
            self.session.add(db_model)
            self.session.commit() #erst commit dann ergibt sich die id für user_obj weil die db dann erst die id vergibt 
            user_obj.id = db_model.id #das logic Objekt hat nun eine id welche nach commit() automatisch von der db zugewiesen wurde, also ist nicht mehr none
            return user_obj #ist das logic Objekt jetzt mit eigener Id nicht mehr none
        except IntegrityError: #wenn Email nicht Unique ist 
            self.session.rollback()
            return None
        except SQLAlchemyError: #allgemeiner fehler 
            self.session.rollback()
            return None

    # CRUD: READ (ALLE MIT FILTER)
    def get_all_users(self, name_filter=None): #none heißt einfach das es standartmäßig alle nutzer anzeigt es dient als Platzhalter für Namen
        query = self.session.query(UserModel)
        #query ist eine Anfrage/Abfrage, indem fall wird in die Tabelle von UserModel mit allen Spalten geschaut
        if name_filter:
            query = query.filter(UserModel.name.ilike(f'%{name_filter}%')) #ilike ist eine suche, das i heißt das es groß und Kleinschreibung ignoriert
            #die % nach ilike heißt egal wo diese folgenden silben vorkommen(hinten/vorne etc.) du zeigst mir dann immer den gesamten Namen 
        db_users = query.all() #hier sehen wir dann alle user nicht nur die mit dem filter 
        
        #es gibt uns eine Liste aus Logic Objekten zurück mithilfe von query.all() was alle Objekte der Spalte von UserModel durchgeht
        return [
            User(name=db_user.name, email=db_user.email, user_id=db_user.id)
            for db_user in db_users
        ] 

    # CRUD: READ (EINZELN)
    def get_user_by_id(self, user_id: int):
            # joinedload sorgt dafür, dass die Posts im "Rucksack" mitkommen
            return self.session.query(UserModel).options(
                joinedload(UserModel.posts) #hiermit sagen wir das wir zusätzlich mit nur einer db anfrage auch die Post des users zur verfügung haben möchten
            ).filter_by(id=user_id).first()
    
    # CRUD: UPDATE (PUT)
    def update_user(self, user_obj): #Platzhalter user_obj
        db_user = self.session.query(UserModel).filter_by(id=user_obj.id).first()
        
        if db_user:
            #hier findet die Überschreibung statt
            #db_user.name etc ist möglich weil wir eine Zeile aus UserModel genommen haben und diese zeile kann nun nach belieben verändert werden
            db_user.name = user_obj.name
            db_user.email = user_obj.email
            
            try:
                self.session.commit()
                return user_obj
            except IntegrityError:
                self.session.rollback()
                return None
            except SQLAlchemyError:
                self.session.rollback()
                return None
        return None

    # CRUD: DELETE
    def delete_user(self, user_id):
        rows_deleted = self.session.query(UserModel).filter_by(id=user_id).delete() #gibt 1 für es wurde was gelöscht und 0 für es wurde nichts gelöscht
        self.session.commit()
        return rows_deleted > 0 #Trich wenn rows_deleted wahr ist ist es eins und es gibt als return wert True zurück wenn nicht False

# REPOSITORY FÜR POSTS (GANZ NEU: Post-CRUD)
class PostRepository:
    def __init__(self, db_session: Session):
        self.session = db_session

    def close(self):
        self.session.close()

    # CRUD: CREATE (POST)
    def save_post(self, post_obj: Post):
        try:
            db_model = PostModel(
                title=post_obj.title, 
                content=post_obj.content, 
                user_id=post_obj.user_id # Hier wird die Beziehung hergestellt
            )
            self.session.add(db_model)
            self.session.commit()
            post_obj.id = db_model.id
            return post_obj
        except IntegrityError: # Fängt Foreign Key Fehler ab (user_id existiert nicht)
            self.session.rollback()
            return None
        except Exception:
            self.session.rollback()
            return None
            
    # CRUD: READ (EINZELN)
    def get_post_by_id(self, post_id: int):
        db_post = self.session.get(PostModel, post_id)
        if db_post is None:
            return None
        return Post(
            title=db_post.title, content=db_post.content, user_id=db_post.user_id, post_id=db_post.id
        )

    # CRUD: READ (ALLE POSTS EINES USERS)
    def get_posts_by_user_id(self, user_id: int):
        posts = self.session.query(PostModel).filter(PostModel.user_id == user_id).all()
        return [
            Post(title=p.title, content=p.content, user_id=p.user_id, post_id=p.id)
            for p in posts
        ]
        
    # CRUD: UPDATE (PUT)
    def update_post(self, post_obj: Post):
        db_post = self.session.get(PostModel, post_obj.id)
        if db_post is None:
            return None
        db_post.title = post_obj.title
        db_post.content = post_obj.content
        try:
            self.session.commit()
            return post_obj
        except Exception:
            self.session.rollback()
            return None

    # CRUD: DELETE
    def delete_post(self, post_id: int):
        db_post = self.session.get(PostModel, post_id)
        if db_post is None:
            return False
        try:
            self.session.delete(db_post)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False
    #um n + 1 Problem zu beheben da die seite sonnst langsam ist
    def get_all_users_with_posts(self):
        # Wir sagen: Query UserModel, aber lade die 'posts' sofort mit!
        users = self.session.query(UserModel).options(joinedload(UserModel.posts)).all()
        return users

# ----------------------------------------------------
# 4. API SCHEMAS (Pydantic) ist für Json format wichtig
# ----------------------------------------------------
#Türsteher für die Außenwelt (meine Apis)
#macht es in den richtigen Format hier Json

# 1. Was der User an uns schickt (EINGABE)
# Was das Frontend schickt (Eingang)
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
'''
doppeltes Sieb damit wir nicht in einer loop landen wegen der author post relationship, deswegen UserResponse und PostSimpleResponse
'''
# 1. Die Sackgasse: Ein Post, der seinen Author NICHT kennt
class PostSimpleResponse(BaseModel):
    id: int
    title: str
    content: str
   
    class Config:
        from_attributes = True

# 2. Das Haupt-Sieb: Ein User, der seine Posts kennt (aber nur die "einfachen")
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    # Hier nutzen wir das Sackgassen-Schema
    posts: List[PostSimpleResponse] = [] #

    class Config:
        from_attributes = True

# 3. Optional: Wenn du NUR einen Post abfragst, darf der ruhig den Author zeigen
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    # Hier könnte man UserModel einbauen, aber meistens reicht die user_id
    class Config:
        from_attributes = True
        #normalerweise ist Pydantic für listen aber das hier sind Objekte deswegen brauchen wir diese Config
#Validierung mit Pydantic:
class PostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100) # Titel MUSS zwischen 3 und 100 Zeichen sein
    content: str = Field(..., min_length=1)               # Inhalt darf nicht leer sein
    user_id: int


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

def get_user_repo(db: Session = Depends(get_db)):
    return UserRepository(db)

def get_post_repo(db: Session = Depends(get_db)):
    return PostRepository(db)

# ----------------------------------------------------
# 5. FASTAPI APP & ENDPUNKTE
# ----------------------------------------------------

app = FastAPI() #das Gehirn der ganzen Sache, sagt Python hier entsteht ein WebServer 

# --- USER ENDPUNKTE (Bisheriger Code) ---

@app.get("/", summary="Basis-Status", tags=["Status"]) # / heißt das ist die Startseite (Hauseingang) == Standart Pfad
def read_root():
    return {"message": "Backend läuft. Gehe zu /docs zum Testen der API."}

# GET /users
@app.get("/users", response_model=List[UserResponse], summary="Alle Benutzer abrufen (Filterbar nach Name)", tags=["Benutzer"]) #/useres (Tür zu Users), 
def get_all_users(name: str | None = None, repo: UserRepository = Depends(get_user_repo)):
   
    users = repo.get_all_users(name_filter=name) 
    
    return users

# GET /users/{user_id}
@app.get("/users/{user_id}", response_model = UserResponse, summary="Einzelnen Benutzer abrufen", tags=["Benutzer"]) #response_model=UserResponse muss da sein es sagt das es dem von UserRespone entsprechen muss
#es kommt also ein Objekt raus was genau so aussieht wie UserResponse 
def get_user(user_id: int, repo: UserRepository = Depends(get_user_repo)):
    user = repo.get_user_by_id(user_id) 
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

# POST /users
@app.post("/users", response_model=UserResponse, summary="Neuen Benutzer erstellen", tags=["Benutzer"])
def create_user(user_data: UserCreate, repo: UserRepository = Depends(get_user_repo)): #die user_datei muss den Typ UserCreate entsprechen weil : UserCreate (Validierung)
   
    new_user_obj = User(name=user_data.name, email=user_data.email)
    
    saved_user = repo.save_user(new_user_obj) #hier wird das user_obj in im UserRepository erstellt und durch das ausgetauscht
    

    if saved_user is None:
        raise HTTPException(status_code=409, detail=f"User with email '{user_data.email}' already exists (Conflict)")
    return saved_user

# PUT /users/{user_id}
@app.put("/users/{user_id}", response_model=UserResponse, summary="Benutzer aktualisieren", tags=["Benutzer"])
def update_user_api(user_id: int, user_data: UserResponse, repo: UserRepository = Depends(get_user_repo)):
   
    user_obj = User(user_id=user_id, name=user_data.name, email=user_data.email)
    updated_user = repo.update_user(user_obj)
    

    if updated_user is None:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found or email conflict.")
            
    return updated_user

# DELETE /users/{user_id}
@app.delete("/users/{user_id}", summary="Benutzer löschen", tags=["Benutzer"]) #packe das in die kategorie tags 
def delete_user_api(user_id: int, repo: UserRepository = Depends(get_user_repo)):
 
    was_deleted = repo.delete_user(user_id)
   

    if not was_deleted:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
    return {"message": f"User with ID {user_id} successfully deleted"}

# --- POST ENDPUNKTE (GANZ NEU: Post-CRUD) ---

# POST /posts
@app.post("/posts", response_model=PostResponse, summary="Neuen Beitrag erstellen", tags=["Beiträge"]) # Response_model bleibt gleich es ist wichtig damit die api später ein Json format sendet
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
@app.get("/posts/{post_id}", response_model=PostResponse, summary="Einzelnen Beitrag abrufen", tags=["Beiträge"])
def get_post(post_id: int, repo: PostRepository = Depends(get_post_repo)):
   
    post = repo.get_post_by_id(post_id)
    

    if post is None:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")

    return post
    
# GET /users/{user_id}/posts (Alle Posts eines Autors) #das users ist das Objekt und die user_id wo gesucht werden soll = Hauptressource
@app.get("/users/{user_id}/posts", response_model=List[PostResponse], summary="Alle Beiträge eines Benutzers abrufen", tags=["Beiträge"])
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
@app.put("/posts/{post_id}", response_model=PostResponse, summary="Beitrag aktualisieren", tags=["Beiträge"])
def update_post_api(post_id: int, post_data: PostResponse, repo: PostRepository = Depends(get_post_repo)):
    post_obj = Post(
        title=post_data.title, content=post_data.content, user_id=post_data.user_id, post_id=post_id
    )

    
    updated_post = repo.update_post(post_obj)
   

    if updated_post is None:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")

    return updated_post #Fast api wandelt das automatisch in PostResponse um 

# DELETE /posts/{post_id}
@app.delete("/posts/{post_id}", status_code=204, summary="Beitrag löschen", tags=["Beiträge"])
def delete_post_api(post_id: int, repo: PostRepository = Depends(get_post_repo)):
   
    was_deleted = repo.delete_post(post_id)


    if not was_deleted:
        raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found.")
        
    return was_deleted  

@app.exception_handler(Exception)
async def global_exception_handler(request, exc): #Globalen Error Handler
    # Das loggt den Fehler für dich in die Konsole
    print(f"KRITISCHER FEHLER: {exc}") 
    return JSONResponse(
        status_code=500,
        content={"message": "Hoppla! Da ist im Maschinenraum etwas schiefgegangen. Wir arbeiten dran."},
    )