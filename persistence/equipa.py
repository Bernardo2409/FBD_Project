# persistence/equipa.py
from typing import NamedTuple, Optional
from pyodbc import IntegrityError
from persistence.session import create_connection


class Equipa(NamedTuple):
    id: str
    nome: str
    orcamento: float
    pontuacao_total: int
    id_utilizador: str


class Pertence(NamedTuple):
    id_equipa: str
    id_jogador: str


def criar_equipa(nome: str, id_utilizador: str) -> str:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Gerar ID único
        cursor.execute("SELECT NEWID()")
        equipa_id = cursor.fetchone()[0]
        
        # Inserir equipa
        cursor.execute("""
            INSERT INTO FantasyChamp.Equipa (ID, Nome, Orçamento, PontuaçãoTotal, ID_Utilizador)
            VALUES (?, ?, 100, 0, ?)
        """, equipa_id, nome, id_utilizador)
        
        conn.commit()
        return equipa_id


def obter_equipa_por_utilizador(id_utilizador: str) -> Optional[Equipa]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Orçamento, PontuaçãoTotal, ID_Utilizador
            FROM FantasyChamp.Equipa
            WHERE ID_Utilizador = ?
        """, id_utilizador)
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return Equipa(
            row.ID,
            row.Nome,
            row.Orçamento,
            row.PontuaçãoTotal,
            row.ID_Utilizador
        )


def obter_jogadores_equipa(id_equipa: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, P.Posição AS Posicao, J.Preço, J.jogador_imagem
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            WHERE PE.ID_Equipa = ?
        """, id_equipa)
        
        jogadores = []
        for row in cursor:
            jogadores.append({
                'id': row.ID,
                'nome': row.Nome,
                'posicao': row.Posicao,
                'preco': row.Preço,
                'jogador_imagem': row.jogador_imagem if row.jogador_imagem 
                          else '/static/images/Image-not-found.png'
            })
        
        return jogadores


def adicionar_jogador_equipa(id_equipa: str, id_jogador: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Pertence 
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        if cursor.fetchone():
            raise IntegrityError("Jogador já está na equipa")
        
        # Inserir relação
        cursor.execute("""
            INSERT INTO FantasyChamp.Pertence (ID_Equipa, ID_Jogador)
            VALUES (?, ?)
        """, id_equipa, id_jogador)
        
        # Atualizar orçamento da equipa
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET Orçamento = (
                SELECT SUM(J.Preço)
                FROM FantasyChamp.Jogador J
                JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
                WHERE PE.ID_Equipa = ?
            )
            WHERE ID = ?
        """, id_equipa, id_equipa)
        
        conn.commit()


def remover_jogador_equipa(id_equipa: str, id_jogador: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Remover relação
        cursor.execute("""
            DELETE FROM FantasyChamp.Pertence 
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        # Atualizar orçamento
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET Orçamento = (
                SELECT SUM(J.Preço)
                FROM FantasyChamp.Jogador J
                JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
                WHERE PE.ID_Equipa = ?
            )
            WHERE ID = ?
        """, id_equipa, id_equipa)
        
        conn.commit()


def verificar_limites_equipa(id_equipa: str) -> dict:
    """Verifica quantos jogadores de cada posição a equipa tem"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT P.Posição, COUNT(*) as count
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            WHERE PE.ID_Equipa = ?
            GROUP BY P.Posição
        """, id_equipa)
        
        contagem = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        for row in cursor:
            contagem[row.Posição] = row.count
        
        return contagem