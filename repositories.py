from sqlalchemy.orm import Session, joinedload
from models import UserModel, PostModel, User, Post  # Wir brauchen die Baupläne
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 



# ----------------------------------------------------
# 3. REPOSITORIES (Küchenchefs)
# ----------------------------------------------------

# REPOSITORY FÜR USER (Hier nur gekürzt, ist in deinem Code enthalten)
class UserRepository:
    def __init__(self, db: Session):
        self.session = db

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
    def __init__(self, db: Session):
        self.session = db

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
