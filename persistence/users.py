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


def create_user_with_ligas(first, last, email, password, country, nationality, birthdate):
    """
    Cria um utilizador e adiciona automaticamente às ligas Mundial e do País.
    Retorna o ID do utilizador se sucesso, None se falhar.
    """
    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        # Executar stored procedure
        cursor.execute("""
            DECLARE @UserID UNIQUEIDENTIFIER, @Sucesso BIT, @Mensagem NVARCHAR(200);
            
            EXEC sp_CriarUtilizadorComLigas
                @PrimeiroNome = ?,
                @Apelido = ?,
                @Email = ?,
                @Senha = ?,
                @Pais = ?,
                @Nacionalidade = ?,
                @DataNascimento = ?,
                @UserID = @UserID OUTPUT,
                @Sucesso = @Sucesso OUTPUT,
                @Mensagem = @Mensagem OUTPUT;
            
            SELECT @UserID, @Sucesso, @Mensagem;
        """, first, last, email, password, country, nationality, birthdate)
        
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            sucesso = result[1]
            mensagem = result[2]
            
            if sucesso:
                conn.commit()
                return user_id
            else:
                conn.rollback()
                raise Exception(mensagem)
        else:
            conn.rollback()
            raise Exception("Nenhum resultado retornado da stored procedure")
            
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Erro de banco de dados: {str(e)}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Mantém a função antiga para compatibilidade
def create_user(first, last, email, password, country, nationality, birthdate):

    try:
        return create_user_with_ligas(first, last, email, password, country, nationality, birthdate)
    except Exception as e:
        print(f"Erro ao criar utilizador: {e}")
        return None

def create_liga_pais(country, creator_id):

    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DECLARE @LigaID UNIQUEIDENTIFIER, @Sucesso BIT, @Mensagem NVARCHAR(200);
            
            EXEC sp_CriarLigaPaisSeNaoExistir
                @Pais = ?,
                @CriadorID = ?,
                @LigaID = @LigaID OUTPUT,
                @Sucesso = @Sucesso OUTPUT,
                @Mensagem = @Mensagem OUTPUT;
            
            SELECT @LigaID, @Sucesso, @Mensagem;
        """, country, creator_id)
        
        result = cursor.fetchone()
        
        if result and result[1]:  # Sucesso = True
            conn.commit()
            return result[0]  # LigaID
        else:
            conn.rollback()
            mensagem = result[2] if result else "Erro desconhecido"
            raise Exception(f"Falha ao criar liga do país: {mensagem}")
            
    except pyodbc.Error as e:
        if conn:
            conn.rollback()
        raise Exception(f"Erro de banco de dados: {str(e)}")
    finally:
        if conn:
            conn.close()

def juntar_liga_automatico(user_id, liga_id):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("EXEC FantasyChamp.sp_JuntarLigaAutomatico ?, ?", user_id, liga_id)
        conn.commit()
        return True