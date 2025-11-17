import time
import requests
import pyodbc
from persistence.session import create_connection

API_KEY = "brEyqEssHcgDFlyANbRxXLUAJAPYFkFitCURYyGxhpc331FYpJ4jt9KNddh6"
BASE_URL = "https://api.sportmonks.com/v3/football/players"


def import_page(page):
    params = {
        "api_token": API_KEY,
        "page": page
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "data" not in data:
        return False

    conn = create_connection()
    cursor = conn.cursor()

    for p in data["data"]:
        player = {
            "id": str(p["id"]),
            "nome": p.get("display_name") or p.get("name"),
            "posicao": str(p.get("position_id")),
            "preco": 0.0,  
            "clube": None, 
            "estado": "EST01",
            "imagem": p.get("image_path")
        }

        try:
            cursor.execute("""
                INSERT INTO FC_Jogador (ID, Nome, Posição, Preço, ID_clube, ID_Estado_Jogador, jogador_imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player["id"], player["nome"], player["posicao"], player["preco"],
                player["clube"], player["estado"], player["imagem"]
            ))
            conn.commit()
            print("[OK]", player["nome"])

        except pyodbc.IntegrityError:
            print("[SKIP] Já existe:", player["nome"])

    return data["pagination"]["has_more"]


def import_all():
    page = 1
    while True:
        print(f" A importar página {page}...")
        has_more = import_page(page)

        if not has_more:
            break

        page += 1
        time.sleep(0.3)


if __name__ == "__main__":
    import_all()
