import pyodbc
from persistence.session import create_connection

def get_users():
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT  U.ID,
                U.PrimeiroNome AS PNome,
                U.Apelido,
                U.Email,
                U.Senha,
                U.País AS Pais,
                U.Nacionalidade,
                U.DataDeNascimento AS BirthDate
        FROM FantasyChamp.Utilizador U
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    users = []
    for row in rows:
        users.append({
            "id": row.ID,
            "FName": row.PNome,
            "LName": row.Apelido,
            "Email": row.Email,
            "Country": row.Pais,
            "Nationality": row.Nacionalidade,
            "BirthDate": row.BirthDate
        })
    
    return users

def login_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT ID, PrimeiroNome, Apelido, Email
        FROM FantasyChamp.Utilizador
        WHERE Email = ? AND Senha = ?
    """

    cursor.execute(query, (email, password))
    row = cursor.fetchone()

    if row:
        return {
            "id": row.ID,
            "first": row.PrimeiroNome,
            "last": row.Apelido,
            "email": row.Email
        }

    return None

def create_user(first, last, email, password, country, nationality, birthdate):
    conn = create_connection()
    cursor = conn.cursor()

    # Cria ID manualmente (SEM usar newid() no SQL)
    cursor.execute("SELECT NEWID()")
    user_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO FantasyChamp.Utilizador
        (ID, PrimeiroNome, Apelido, Email, Senha, País, Nacionalidade, DataDeNascimento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, first, last, email, password, country, nationality, birthdate))

    conn.commit()
    return user_id


def get_user_by_id(user_id):
    """Retorna um dicionário com os dados do utilizador ou None se não existir."""
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT ID, PrimeiroNome, Apelido, Email, País AS Pais, Nacionalidade, DataDeNascimento
        FROM FantasyChamp.Utilizador
        WHERE ID = ?
    """

    cursor.execute(query, (user_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row.ID,
        "first": row.PrimeiroNome,
        "last": row.Apelido,
        "email": row.Email,
        "pais": row.Pais,
        "nationality": row.Nacionalidade,
        "birthdate": row.DataDeNascimento,
    }
