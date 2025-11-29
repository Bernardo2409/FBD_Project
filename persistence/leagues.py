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
    nome_criador: Optional[str] = None


class Participa(NamedTuple):
    id_utilizador: str
    id_liga: str


class TipoLiga(NamedTuple):
    id: str
    tipo: str


# --------------------------------------------------------------------
# ⚡ Criar liga privada
# --------------------------------------------------------------------
def criar_liga(nome: str, data_inicio: str, data_fim: str,
               id_tipo_liga: str = 'LT02', id_criador: str = None,
               codigo_convite: Optional[str] = None) -> str:

    with create_connection() as conn:
        cursor = conn.cursor()

        liga_id = str(uuid.uuid4())

        # Use placeholders for all values and pass id_tipo_liga explicitly.
        cursor.execute("""
            INSERT INTO FantasyChamp.Liga
            (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, liga_id, nome, data_inicio, data_fim, id_tipo_liga, id_criador, codigo_convite)

        # Criador entra automaticamente (se fornecido)
        if id_criador:
            cursor.execute("""
                INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
                VALUES (?, ?)
            """, id_criador, liga_id)

        conn.commit()

        return liga_id


# --------------------------------------------------------------------
# ⚡ Criar liga pública "automática" (Mundial e país do utilizador)
# --------------------------------------------------------------------
def criar_liga_publica(nome_liga: str, id_criador: str = None) -> str:
    """Cria liga pública sem código, usada para Mundial + países."""
    with create_connection() as conn:
        cursor = conn.cursor()

        liga_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO FantasyChamp.Liga
            (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES (?, ?, GETDATE(), '2100-01-01', 'LT01', ?, NULL)
        """, liga_id, nome_liga, id_criador)

        # Criador entra automaticamente (se existir)
        if id_criador:
            cursor.execute("""
                INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
                VALUES (?, ?)
            """, id_criador, liga_id)

        conn.commit()

        return liga_id


# --------------------------------------------------------------------
# ⚡ Obter tipos de liga
# --------------------------------------------------------------------
def obter_tipos_liga() -> List[TipoLiga]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Tipo
            FROM FantasyChamp.Tipo_Liga
            ORDER BY ID
        """)

        return [TipoLiga(row.ID, row.Tipo) for row in cursor]


# --------------------------------------------------------------------
# ⚡ Obter ligas onde o utilizar participa
# --------------------------------------------------------------------
def obter_ligas_por_utilizador(id_utilizador: str) -> List[Liga]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT L.ID, L.Nome, L.Data_Inicio, L.Data_Fim,
                   L.ID_tipoLiga, L.ID_criador, L.Código_Convite
            FROM FantasyChamp.Liga L
            JOIN FantasyChamp.Participa P ON L.ID = P.ID_Liga
            WHERE P.ID_Utilizador = ?
        """, id_utilizador)

        return [
            Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim,
                 row.ID_tipoLiga, row.ID_criador, row.Código_Convite)
            for row in cursor
        ]


# --------------------------------------------------------------------
# ⚡ Obter liga por ID
# --------------------------------------------------------------------
def obter_liga_por_id(id_liga: str) -> Optional[Liga]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Data_Inicio, Data_Fim,
                   ID_tipoLiga, ID_criador, Código_Convite
            FROM FantasyChamp.Liga
            WHERE ID = ?
        """, id_liga)

        row = cursor.fetchone()
        return Liga(*row) if row else None


# --------------------------------------------------------------------
# ⚡ Obter liga pelo nome (ex: "Portugal" ou "Mundial")
# --------------------------------------------------------------------
def obter_liga_pelo_pais(nome_liga: str) -> Optional[Liga]:
    with create_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ID, Nome, Data_Inicio, Data_Fim,
                   ID_tipoLiga, ID_criador, Código_Convite
            FROM FantasyChamp.Liga
            WHERE Nome = ? AND ID_tipoLiga = 'LT01'
        """, nome_liga)

        row = cursor.fetchone()
        return Liga(*row) if row else None


# --------------------------------------------------------------------
# ⚡ User junta-se automaticamente a uma liga
# --------------------------------------------------------------------
def juntar_liga_automatico(id_utilizador: str, liga: Liga):
    with create_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Participa
            WHERE ID_Utilizador = ? AND ID_Liga = ?
        """, id_utilizador, liga.id)

        if cursor.fetchone():
            return  # já está na liga

        cursor.execute("""
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (?, ?)
        """, id_utilizador, liga.id)

        conn.commit()


# --------------------------------------------------------------------
# ⚡ Juntar a liga manual (com código, se privado)
# --------------------------------------------------------------------
def juntar_liga(id_utilizador: str, id_liga: str, codigo: Optional[str]) -> bool:
    with create_connection() as conn:
        cursor = conn.cursor()

        # Verificar se já está
        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Participa
            WHERE ID_Utilizador = ? AND ID_Liga = ?
        """, id_utilizador, id_liga)

        if cursor.fetchone():
            return False

        # Verificar tipo + código
        cursor.execute("""
            SELECT ID_tipoLiga, Código_Convite
            FROM FantasyChamp.Liga
            WHERE ID = ?
        """, id_liga)

        info = cursor.fetchone()

        if info.ID_tipoLiga == 'LT02':  # privada
            if not codigo or codigo != info.Código_Convite:
                return False

        # Entrar
        cursor.execute("""
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (?, ?)
        """, id_utilizador, id_liga)

        conn.commit()
        return True


# --------------------------------------------------------------------
# ⚡ Obter participantes de uma liga
# --------------------------------------------------------------------
def obter_participantes_liga(id_liga: str):
    """Obtém todos os participantes de uma liga, excluindo o 'Sistema'"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT U.ID, U.PrimeiroNome, U.Apelido, U.Email, E.Nome as NomeEquipa
            FROM FantasyChamp.Utilizador U
            JOIN FantasyChamp.Participa P ON U.ID = P.ID_Utilizador
            LEFT JOIN FantasyChamp.Equipa E ON U.ID = E.ID_Utilizador
            WHERE P.ID_Liga = ? AND U.PrimeiroNome != 'Sistema'
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



# --------------------------------------------------------------------
# ⚡ Ligas públicas visíveis para o utilizador
#    → Mundial + Liga do país do user
#    → EXCLUINDO ligas onde o user já participa
# --------------------------------------------------------------------
def obter_ligas_publicas_para_utilizador(user_country: str, id_user: str):
    with create_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT L.ID, L.Nome, L.Data_Inicio, L.Data_Fim,
                   L.ID_tipoLiga, L.ID_criador, L.Código_Convite,
                   U.PrimeiroNome
            FROM FantasyChamp.Liga L
            JOIN FantasyChamp.Utilizador U ON L.ID_criador = U.ID
            WHERE 
                L.ID_tipoLiga = 'LT01'
                AND L.Data_Fim > GETDATE()
                AND L.Nome IN ('Mundial', ?)
                AND L.ID NOT IN (
                    SELECT ID_Liga FROM FantasyChamp.Participa
                    WHERE ID_Utilizador = ?
                )
            ORDER BY L.Nome
        """, user_country, id_user)

        return [
            Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim,
                 row.ID_tipoLiga, row.ID_criador,
                 row.Código_Convite, row.PrimeiroNome)
            for row in cursor
        ]


# --------------------------------------------------------------------
# ⚡ Obter ID da liga a partir do código de convite
# --------------------------------------------------------------------
def obter_liga_id_por_codigo(codigo: str) -> Optional[str]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID FROM FantasyChamp.Liga
            WHERE Código_Convite = ?
        """, codigo)
        row = cursor.fetchone()
        return row.ID if row else None


# --------------------------------------------------------------------
# ⚡ Abandonar liga
# --------------------------------------------------------------------
def abandonar_liga(id_utilizador: str, id_liga: str) -> bool:
    with create_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Participa
            WHERE ID_Utilizador = ? AND ID_Liga = ?
        """, id_utilizador, id_liga)

        if not cursor.fetchone():
            return False

        cursor.execute("""
            DELETE FROM FantasyChamp.Participa
            WHERE ID_Utilizador = ? AND ID_Liga = ?
        """, id_utilizador, id_liga)

        conn.commit()
        return True
