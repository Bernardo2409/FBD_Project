# persistence/countries.py
from persistence.session import create_connection

def get_pais():
    """Recupera todos os países e suas imagens da base de dados"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, imagem FROM FantasyChamp.Pais")  # Tabela Pais com as colunas nome e imagem
        pais = [{'nome': row.nome, 'imagem': row.imagem} for row in cursor.fetchall()]
    return pais
