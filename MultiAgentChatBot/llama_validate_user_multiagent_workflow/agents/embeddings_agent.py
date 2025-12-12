from sentence_transformers import SentenceTransformer
from utils.helpers import cosine_similarity
from utils.config import SIMILARITY_THRESHOLD

# Simple in-memory store
user_store = {}
VECTOR_FIELD = "embedding"
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def add_or_update_user(email,user_name,user_info):
    combined_info = f"{user_name}: {user_info}"  # Club username and info
    vector = embed_model.encode(combined_info).tolist()
    user_store[email] = {"info": combined_info, VECTOR_FIELD: vector}

def is_existing_user(email):
    return email in user_store

def delete_user(email):
    if email in user_store:
        del user_store[email]
        return True
    return False

def semantic_name_search(new_name,new_info, threshold=SIMILARITY_THRESHOLD):
    combined_info = f"{new_name}: {new_info}"  # Club username and info
    new_vec = embed_model.encode(combined_info).tolist()
    similar_users = []
    for email, data in user_store.items():
        sim = cosine_similarity(new_vec, data[VECTOR_FIELD])
        if sim >= threshold:
            similar_users.append((email, sim))
    return similar_users
