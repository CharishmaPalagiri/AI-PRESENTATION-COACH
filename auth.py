import chromadb
import hashlib
import os
import uuid
from datetime import datetime

# Data is stored in the "chroma_store" folder
client = chromadb.PersistentClient(path="chroma_store")

# embedding_function=None -> no model download, works offline
users = client.get_or_create_collection("users", embedding_function=None)
sessions = client.get_or_create_collection("sessions", embedding_function=None)

# ChromaDB needs a vector; we do not use embeddings, so we store a dummy one
DUMMY = [0.0] * 384


def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()


def register_user(username, password):
    """Returns True if the account was created, False if the username exists."""
    username = username.strip().lower()
    if users.get(ids=[username])["ids"]:
        return False
    salt = os.urandom(8).hex()
    users.add(
        ids=[username],
        documents=[username],
        embeddings=[DUMMY],
        metadatas=[{"salt": salt, "hash": hash_password(password, salt)}],
    )
    return True


def login_user(username, password):
    """Returns True if the username and password are correct."""
    username = username.strip().lower()
    result = users.get(ids=[username])
    if not result["ids"]:
        return False
    meta = result["metadatas"][0]
    return hash_password(password, meta["salt"]) == meta["hash"]


def save_session(username, title, text, stats, feedback):
    """Saves one practice session for the user."""
    sessions.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        embeddings=[DUMMY],
        metadatas=[{
            "username": username,
            "title": title,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "words": stats["words"],
            "minutes": stats["minutes"],
            "fillers": stats["fillers"],
            "feedback": feedback,
        }],
    )


def get_sessions(username):
    """Returns all sessions of the user, newest first."""
    result = sessions.get(where={"username": username})
    return sorted(result["metadatas"], key=lambda m: m["created"], reverse=True)