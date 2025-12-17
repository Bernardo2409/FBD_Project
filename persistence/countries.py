# persistence/countries.py
from persistence.session import create_connection

def get_pais():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, imagem FROM FantasyChamp.PaisView")
        pais = [{'nome': row.nome, 'imagem': row.imagem} for row in cursor.fetchall()]
    return pais