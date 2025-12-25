from pydantic import BaseModel, EmailStr, Field
from typing import List

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

