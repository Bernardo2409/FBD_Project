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
    jogador_imagem: str


class PlayerDetails(NamedTuple):
    id: str
    nome: str
    posicao: str
    preco: float
    nome_clube: str
    id_estado: str
    Clube_id: str
    clube_imagem: str
    jogador_imagem: str


# --- CRUD FUNCTIONS ---

def list_all() -> list[PlayerDescriptor]:
    """
    Lista todos os jogadores com descrição curta.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Posição, Preço, jogador_imagem
            FROM FC_Jogador;
        """)

        return list(map(
            lambda row: PlayerDescriptor(row.ID, row.Nome, row.Posição, row.Preço, row.jogador_imagem if row.jogador_imagem else '/static/images/Image-not-found.png'),
            cursor
        ))


def read(j_id: str):
    """
    Lê todos os detalhes de um jogador específico, incluindo o nome do clube e a imagem do clube.
    Se a imagem do clube for NULL, será usada uma imagem padrão.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, J.Posição, J.Preço, J.jogador_imagem, C.Nome AS Clube, C.clube_imagem, C.ID AS Clube_id, E.Estado
            FROM FC_Jogador J
            JOIN FC_Clube C ON J.ID_clube = C.ID
            JOIN FC_Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            WHERE J.ID = ?;
        """, j_id)

        row = cursor.fetchone()
        if not row:
            return None

        # Se a imagem do clube for NULL, define uma imagem padrão
        clube_imagem = row.clube_imagem if row.clube_imagem else '/static/images/Image-not-found.png'
        jogador_imagem = row.jogador_imagem if row.jogador_imagem else '/static/images/Image-not-found.png'

        print(f"Imagem do clube: {clube_imagem}")

        return PlayerDetails(
            row.ID,
            row.Nome,
            row.Posição,
            row.Preço,
            row.Clube, 
            row.Estado,
            row.Clube_id,
            clube_imagem,
            jogador_imagem
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
