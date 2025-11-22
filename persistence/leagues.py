# persistence/ligas.py
from typing import NamedTuple, Optional, List
from persistence.session import create_connection
import uuid
from datetime import datetime

class Liga(NamedTuple):
    id: str
    nome: str
    data_inicio: str
    data_fim: str
    id_tipo_liga: str
    id_criador: str
    codigo_convite: Optional[str] = None 

class Participa(NamedTuple):
    id_utilizador: str
    id_liga: str

class TipoLiga(NamedTuple):
    id: str
    tipo: str  

def criar_liga(nome: str, data_inicio: str, data_fim: str, id_tipo_liga: str, id_criador: str, codigo_convite: Optional[str] = None) -> str:
    """Cria uma nova liga e adiciona o criador como participante"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Gerar ID único para a liga
        liga_id = str(uuid.uuid4())
        
        # Inserir liga
        cursor.execute("""
            INSERT INTO FantasyChamp.Liga (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, liga_id, nome, data_inicio, data_fim, id_tipo_liga, id_criador, codigo_convite)  
        
        # Adicionar criador como participante
        cursor.execute("""
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (?, ?)
        """, id_criador, liga_id)
        
        conn.commit()
        return liga_id

def obter_tipos_liga() -> List[TipoLiga]:
    """Obtém todos os tipos de liga disponíveis"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Tipo 
            FROM FantasyChamp.Tipo_Liga
            ORDER BY ID
        """)
        
        tipos = []
        for row in cursor:
            print(f"Tipo encontrado: ID={row.ID}, Tipo={row.Tipo}")  # Debug
            tipos.append(TipoLiga(row.ID, row.Tipo))
        
        return tipos

def obter_ligas_por_utilizador(id_utilizador: str) -> List[Liga]:
    """Obtém todas as ligas em que o utilizador participa"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT L.ID, L.Nome, L.Data_Inicio, L.Data_Fim, L.ID_tipoLiga, L.ID_criador, L.Código_Convite
            FROM FantasyChamp.Liga L
            JOIN FantasyChamp.Participa P ON L.ID = P.ID_Liga
            WHERE P.ID_Utilizador = ?
        """, id_utilizador)
        
        ligas = []
        for row in cursor:
            print(f"Liga do utilizador: {row.Nome} - Tipo: {row.ID_tipoLiga} - Código: {row.Código_Convite}")
            ligas.append(Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim, row.ID_tipoLiga, row.ID_criador, row.Código_Convite))
        
        return ligas

def obter_liga_por_id(id_liga: str) -> Optional[Liga]:
    """Obtém uma liga específica pelo ID"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite
            FROM FantasyChamp.Liga
            WHERE ID = ?
        """, id_liga)
        
        row = cursor.fetchone()
        if row:
            return Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim, row.ID_tipoLiga, row.ID_criador, row.Código_Convite)
        return None

def juntar_liga(id_utilizador: str, id_liga: str, codigo: Optional[str] = None) -> bool:
    """Adiciona um utilizador a uma liga"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar se já é participante
        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Participa 
            WHERE ID_Utilizador = ? AND ID_Liga = ?
        """, id_utilizador, id_liga)
        
        if cursor.fetchone():
            return False  # Já está na liga
        
        # Verificar se a liga é privada e requer código
        cursor.execute("""
            SELECT ID_tipoLiga, Código_Convite FROM FantasyChamp.Liga WHERE ID = ?
        """, id_liga)
        
        liga = cursor.fetchone()
        if not liga:
            return False
        
        # Se for liga privada, verificar código
        if liga.ID_tipoLiga == 'LT02':  # LT02 = Privada
            if not codigo or codigo != liga.Código_Convite:
                return False  # Código incorreto ou não fornecido
        
        # Adicionar à liga
        cursor.execute("""
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (?, ?)
        """, id_utilizador, id_liga)
        
        conn.commit()
        return True

def obter_participantes_liga(id_liga: str):
    """Obtém todos os participantes de uma liga"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT U.ID, U.PrimeiroNome, U.Apelido, U.Email, E.Nome as NomeEquipa
            FROM FantasyChamp.Utilizador U
            JOIN FantasyChamp.Participa P ON U.ID = P.ID_Utilizador
            LEFT JOIN FantasyChamp.Equipa E ON U.ID = E.ID_Utilizador
            WHERE P.ID_Liga = ?
        """, id_liga)
        
        participantes = []
        for row in cursor:
            participantes.append({
                'id': row.ID,
                'nome': f"{row.PrimeiroNome} {row.Apelido}",
                'email': row.Email,
                'equipa': row.NomeEquipa
            })
        
        return participantes

def obter_ligas_publicas() -> List[Liga]:
    """Obtém ligas públicas para os utilizadores se juntarem"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite
            FROM FantasyChamp.Liga
            WHERE ID_tipoLiga = 'LT01' AND Data_Fim > GETDATE()
            ORDER BY Data_Inicio DESC
        """)
        
        ligas = []
        for row in cursor:
            print(f"Liga pública encontrada: {row.Nome} - Tipo: {row.ID_tipoLiga} - Código: {row.Código_Convite}")
            ligas.append(Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim, row.ID_tipoLiga, row.ID_criador, row.Código_Convite))
        
        return ligas