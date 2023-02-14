import requests
from hashlib import sha512

SERVER_IP = "130.61.30.242"
SERVER_PORT = 20238

def create_hash(text: str) -> str:
    """Vytvoří hash pro rádoby bezpečnější přenos dat."""
    text += "uloha8priponysouboru"
    return sha512(text.encode("utf-8")).hexdigest()

def server_set(username: str, progress: int) -> bool:
    """Odešle postup na server."""
    try:
        r = requests.put(f"http://{SERVER_IP}:{SERVER_PORT}/?username={username}&progress={progress}&hash={create_hash(username+str(progress))}", timeout=(10,15))
        if r.status_code in range(200, 300):
            return True
        return False
    except requests.exceptions.ConnectionError:
        print("Odeslání dat na server selhalo")
    return False

def server_get(username: str) -> int:
    """Načte postup ze serveru."""
    try:
        r = requests.get(f"http://{SERVER_IP}:{SERVER_PORT}/?username={username}&hash={create_hash(username)}", timeout=(10,15))
        if r.status_code in range(200, 300):
            return int(r.text)
        return int(r.text)
    except requests.exceptions.ConnectionError:
        print("Stažení dat ze serveru selhalo")
    return -1
