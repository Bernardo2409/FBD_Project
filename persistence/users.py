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