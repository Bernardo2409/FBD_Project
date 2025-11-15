import random
import string
from typing import NamedTuple

from pyodbc import IntegrityError
from persistence.session import create_connection


# --- DATA MODELS ---

class PlayerDescriptor(NamedTuple):
    id: str
    nome: str
    posicao: str
    preco: float


class PlayerDetails(NamedTuple):
    nome: str
    posicao: str
    preco: float
    id_clube: str
    id_estado: str


# --- CRUD FUNCTIONS ---

def list_all() -> list[PlayerDescriptor]:
    """
    Lista todos os jogadores com descrição curta.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Posição, Preço
            FROM FC_Jogador;
        """)

        return list(map(
            lambda row: PlayerDescriptor(row.ID, row.Nome, row.Posição, row.Preço),
            cursor
        ))


def read(j_id: str):
    """
    Lê todos os detalhes de um jogador específico, incluindo o nome do clube.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, J.Posição, J.Preço, C.Nome AS Clube, E.Estado
            FROM FC_Jogador J
            JOIN FC_Clube C ON J.ID_clube = C.ID
            JOIN FC_Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            WHERE J.ID = ?;
        """, j_id)

        row = cursor.fetchone()
        if not row:
            return None

        return row.ID, PlayerDetails(
            row.Nome,
            row.Posição,
            row.Preço,
            row.Clube,  # Agora o nome do clube
            row.Estado  # Estado do jogador
        )



def create(jogador: PlayerDetails):
    """
    Cria um novo jogador com ID aleatório (8 chars).
    """
    id_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO FC_Jogador(
                ID, Nome, Posição, Preço, ID_clube, ID_Estado_Jogador
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            id_str,
            jogador.nome,
            jogador.posicao,
            jogador.preco,
            jogador.id_clube,
            jogador.id_estado
        )

        cursor.commit()


def update(j_id: str, jogador: PlayerDetails):
    """
    Atualiza um jogador existente.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE FC_Jogador
            SET Nome = ?,
                Posição = ?,
                Preço = ?,
                ID_clube = ?,
                ID_Estado_Jogador = ?
            WHERE ID = ?;
            """,
            jogador.nome,
            jogador.posicao,
            jogador.preco,
            jogador.id_clube,
            jogador.id_estado,
            j_id
        )

        cursor.commit()


def delete(j_id: str):
    """
    Apaga um jogador (se não violar integridade referencial).
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM FC_Jogador WHERE ID = ?;", j_id)
            cursor.commit()
        except IntegrityError as ex:
            # Código genérico de violação FK no SQL Server
            if ex.args[0] == "23000":
                raise Exception(
                    f"Jogador {j_id} não pode ser apagado. "
                    f"Provavelmente está associado a jornadas / equipas."
                ) from ex
