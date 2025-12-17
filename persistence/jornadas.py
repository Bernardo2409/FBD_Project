from persistence.session import create_connection
import pyodbc

def obter_jornada_info(id_jornada: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ID, Numero, Data_Inicio, Data_Fim
                FROM FantasyChamp.Jornada
                WHERE ID = ?
            """, id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'numero': row[1],
                    'data_inicio': row[2],
                    'data_fim': row[3]
                }
            else:
                return None
                
        except pyodbc.Error as e:
            print(f"Erro ao obter jornada info: {e}")
            return None

def obter_jornada_atual() -> dict:

    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("EXEC FantasyChamp.ObterJornadaAtual")
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': str(row.ID),
                'numero': int(row.Numero) if row.Numero else 0
            }
        
        return None

def obter_todas_jornadas():
    """
    Obtém todas as jornadas.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ID, Numero, Data_Inicio, Data_Fim
                FROM FantasyChamp.Jornada
                ORDER BY Numero
            """)
            
            rows = cursor.fetchall()
            
            jornadas = []
            for row in rows:
                jornadas.append({
                    'id': row[0],
                    'numero': row[1],
                    'data_inicio': row[2],
                    'data_fim': row[3]
                })
            
            return jornadas
                
        except pyodbc.Error as e:
            print(f"Erro ao obter todas jornadas: {e}")
            return []