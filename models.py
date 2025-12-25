from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from datenbase import Base # Import von oben!


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
