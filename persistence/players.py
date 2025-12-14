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
    estado: str


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


class PlayerStats(NamedTuple):
    id_jornada: str
    pontuacao_total: int
    golos_marcados: int
    assistencias: int
    cartoes_amarelos: int
    cartoes_vermelhos: int
    tempo_jogo: int


# --- CRUD FUNCTIONS ---

def list_all() -> list[PlayerDescriptor]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, P.Posição AS Posicao, J.Preço, J.jogador_imagem, E.Estado
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID; 
        """)

        return list(map(
            lambda row:
                PlayerDescriptor(
                    row.ID,
                    row.Nome,
                    row.Posicao,
                    row.Preço,
                    row.jogador_imagem if row.jogador_imagem
                    else '/static/images/Image-not-found.png',
                    row.Estado
                ),
            cursor
        ))


def read(j_id: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                J.ID, 
                J.Nome, 
                P.Posição AS Posicao,
                J.Preço,
                J.jogador_imagem,
                C.Nome AS Clube,
                C.clube_imagem,
                C.ID AS Clube_id,
                E.Estado
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
            JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE J.ID = ?;
        """, j_id)

        row = cursor.fetchone()
        if not row:
            return None

        return PlayerDetails(
            row.ID,
            row.Nome,
            row.Posicao,
            row.Preço,
            row.Clube,
            row.Estado,
            row.Clube_id,
            row.clube_imagem if row.clube_imagem else '/static/images/Image-not-found.png',
            row.jogador_imagem if row.jogador_imagem else '/static/images/Image-not-found.png'
        )


def get_player_stats(j_id: str) -> tuple[list[PlayerStats], int]:
    """
    Obtém as estatísticas do jogador por jornada e a pontuação total
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Buscar estatísticas por jornada
        cursor.execute("""
            SELECT 
                ID_jornada,
                pontuação_total,
                GolosMarcados,
                Assistencias,
                CartoesAmarelos,
                CartoesVermelhos,
                TempoJogo
            FROM FantasyChamp.Pontuação_Jogador
            WHERE ID_jogador = ?
            ORDER BY ID_jornada
        """, j_id)
        
        stats = []
        total_pontos = 0
        
        for row in cursor:
            # Converter valores para garantir tipos corretos
            pontuacao = int(row.pontuação_total) if row.pontuação_total is not None else 0
            golos = int(row.GolosMarcados) if row.GolosMarcados is not None else 0
            assistencias = int(row.Assistencias) if row.Assistencias is not None else 0
            amarelos = int(row.CartoesAmarelos) if row.CartoesAmarelos is not None else 0
            vermelhos = int(row.CartoesVermelhos) if row.CartoesVermelhos is not None else 0
            minutos = int(row.TempoJogo) if row.TempoJogo is not None else 0
            
            stats.append(PlayerStats(
                row.ID_jornada,
                pontuacao,
                golos,
                assistencias,
                amarelos,
                vermelhos,
                minutos
            ))
            total_pontos += pontuacao
        
        return stats, total_pontos


def list_paginated(page: int, per_page: int) -> tuple[list[PlayerDescriptor], int]:
    offset = (page - 1) * per_page

    with create_connection() as conn:
        cursor = conn.cursor()

        # total de jogadores
        cursor.execute("SELECT COUNT(*) FROM FantasyChamp.Jogador;")
        total = cursor.fetchone()[0]

        # query paginada
        cursor.execute(f"""
            SELECT J.ID, J.Nome, P.Posição AS Posicao, J.Preço, J.jogador_imagem, E.Estado
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID 
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            ORDER BY J.Nome
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;
        """)

        jogadores = list(map(
            lambda row: PlayerDescriptor(
                row.ID,
                row.Nome,
                row.Posicao,
                row.Preço,
                row.jogador_imagem if row.jogador_imagem
                else '/static/images/Image-not-found.png',
                row.Estado
            ),
            cursor
        ))

    return jogadores, total