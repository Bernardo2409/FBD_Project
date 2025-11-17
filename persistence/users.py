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

    query = """
        INSERT INTO FantasyChamp.Utilizador
        (ID, PrimeiroNome, Apelido, Email, Senha, País, Nacionalidade, DataDeNascimento)
        VALUES (NEWID(), ?, ?, ?, ?, ?, ?, ?)
    """

    cursor.execute(query, (first, last, email, password, country, nationality, birthdate))
    conn.commit()