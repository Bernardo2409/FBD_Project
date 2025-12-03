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
    benched: bool


def criar_equipa(nome: str, id_utilizador: str) -> str:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Gerar ID único
        cursor.execute("SELECT NEWID()")
        equipa_id = cursor.fetchone()[0]
        
        # Inserir equipa com orçamento inicial de 100
        cursor.execute("""
            INSERT INTO FantasyChamp.Equipa (ID, Nome, Orçamento, PontuaçãoTotal, ID_Utilizador)
            VALUES (?, ?, 100.00, 0, ?)
        """, equipa_id, nome, id_utilizador)
        
        conn.commit()
        return equipa_id


def obter_preco_jogador(id_jogador: str) -> float:
    """Obter o preço de um jogador"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Preço FROM FantasyChamp.Jogador WHERE ID = ?
        """, id_jogador)
        
        row = cursor.fetchone()
        return row.Preço if row else 0

def verificar_orcamento_suficiente(id_equipa: str, preco_jogador: float) -> bool:
    """Verificar se a equipa tem orçamento suficiente"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Orçamento FROM FantasyChamp.Equipa WHERE ID = ?
        """, id_equipa)
        
        row = cursor.fetchone()
        orcamento_atual = row.Orçamento if row else 0
        return orcamento_atual >= preco_jogador
    
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
            SELECT J.ID, J.Nome, P.Posição AS Posicao, J.Preço, J.jogador_imagem, E.Estado, PE.benched
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
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
                          else '/static/images/Image-not-found.png',
                'estado': row.Estado,
                'benched': True if row.benched == 1 else False
            })
        
        return jogadores


def obter_posicao_jogador(id_jogador: str) -> str:
    """Obter a posição de um jogador"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT P.Posição
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE J.ID = ?
        """, id_jogador)
        
        row = cursor.fetchone()
        return row.Posição if row else None


def contar_jogadores_por_posicao(id_equipa: str, apenas_campo: bool = False):
    """Contar jogadores por posição (no campo ou total)"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT P.Posição, COUNT(*) as count
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            WHERE PE.ID_Equipa = ?
        """
        
        if apenas_campo:
            query += " AND PE.benched = 0"
        
        query += " GROUP BY P.Posição"
        
        cursor.execute(query, id_equipa)
        
        contagem = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        for row in cursor:
            contagem[row.Posição] = row.count
        
        return contagem


def adicionar_jogador_equipa(id_equipa: str, id_jogador: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar se já existe
        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Pertence 
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        if cursor.fetchone():
            raise Exception("Jogador já está na equipa")
        
        # Obter preço do jogador
        preco_jogador = obter_preco_jogador(id_jogador)
        
        # Verificar se tem orçamento suficiente
        if not verificar_orcamento_suficiente(id_equipa, preco_jogador):
            raise Exception("Orçamento insuficiente para adicionar este jogador")
        
        # Inserir relação (por padrão benched=0, ou seja, em campo)
        cursor.execute("""
            INSERT INTO FantasyChamp.Pertence (ID_Equipa, ID_Jogador, benched)
            VALUES (?, ?, 0)
        """, id_equipa, id_jogador)
        
        # Subtrair o preço do jogador ao orçamento
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET Orçamento = Orçamento - ?
            WHERE ID = ?
        """, preco_jogador, id_equipa)
        
        conn.commit()


def remover_jogador_equipa(id_equipa: str, id_jogador: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter preço do jogador antes de remover
        preco_jogador = obter_preco_jogador(id_jogador)
        
        # Remover relação
        cursor.execute("""
            DELETE FROM FantasyChamp.Pertence 
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        # Devolver o preço ao orçamento
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET Orçamento = Orçamento + ?
            WHERE ID = ?
        """, preco_jogador, id_equipa)
        
        conn.commit()


def verificar_limites_equipa(id_equipa: str) -> dict:
    """Verifica quantos jogadores de cada posição a equipa tem e se pode adicionar mais"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Contar jogadores por posição
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
        
        # Obter orçamento atual
        cursor.execute("SELECT Orçamento FROM FantasyChamp.Equipa WHERE ID = ?", id_equipa)
        row = cursor.fetchone()
        orcamento_atual = row.Orçamento if row else 0
        
        return {
            'contagem': contagem,
            'orcamento': orcamento_atual,
            'pode_adicionar_gr': contagem['Goalkeeper'] < 2,
            'pode_adicionar_defesa': contagem['Defender'] < 5,
            'pode_adicionar_medio': contagem['Midfielder'] < 5,
            'pode_adicionar_avancado': contagem['Forward'] < 3
        }


def adicionar_jogador_ao_banco(id_equipa: str, id_jogador: str) -> tuple[bool, str]:
    """
    Adiciona um jogador ao banco.
    Retorna (sucesso, mensagem)
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter posição do jogador
        posicao = obter_posicao_jogador(id_jogador)
        if not posicao:
            return False, "Jogador não encontrado"
        
        # Contar jogadores em campo por posição
        contagem_campo = contar_jogadores_por_posicao(id_equipa, apenas_campo=True)
        
        # Verificar se há pelo menos 1 jogador em campo dessa posição
        if contagem_campo[posicao] <= 1:
            return False, f"Deve haver pelo menos 1 {posicao} em campo!"
        
        # Verificar limites mínimos em campo
        if posicao == 'Goalkeeper' and contagem_campo['Goalkeeper'] <= 1:
            return False, "Deve haver pelo menos 1 guarda-redes em campo!"
        elif posicao == 'Forward' and contagem_campo['Forward'] <= 1:
            return False, "Deve haver pelo menos 1 avançado em campo!"
        elif posicao == 'Midfielder' and contagem_campo['Midfielder'] <= 1:
            return False, "Deve haver pelo menos 1 médio em campo!"
        elif posicao == 'Defender' and contagem_campo['Defender'] <= 1:
            return False, "Deve haver pelo menos 1 defesa em campo!"
        
        # Contar jogadores no banco
        cursor.execute("""
            SELECT COUNT(*) FROM FantasyChamp.Pertence
            WHERE ID_Equipa = ? AND benched = 1
        """, id_equipa)
        
        total_banco = cursor.fetchone()[0]
        
        # Verificar se já tem 4 jogadores no banco
        if total_banco >= 4:
            return False, "Já tens 4 jogadores no banco!"
        
        # Atualizar o jogador para banco
        cursor.execute("""
            UPDATE FantasyChamp.Pertence 
            SET benched = 1
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        conn.commit()
        return True, "Jogador movido para o banco com sucesso!"


def remover_jogador_do_banco(id_equipa: str, id_jogador: str) -> tuple[bool, str]:
    """
    Remove um jogador do banco (coloca-o em campo).
    Retorna (sucesso, mensagem)
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter posição do jogador
        posicao = obter_posicao_jogador(id_jogador)
        if not posicao:
            return False, "Jogador não encontrado"
        
        # Contar jogadores no banco
        cursor.execute("""
            SELECT COUNT(*) FROM FantasyChamp.Pertence
            WHERE ID_Equipa = ? AND benched = 1
        """, id_equipa)
        
        total_banco = cursor.fetchone()[0]
        
        # Verificar se tem pelo menos 4 jogadores no banco
        if total_banco <= 4:
            return False, "Deve haver pelo menos 4 jogadores no banco!"
        
        # Verificar se tem pelo menos 1 GR no banco
        cursor.execute("""
            SELECT COUNT(*) FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = ? AND PE.benched = 1 AND P.Posição = 'Goalkeeper'
        """, id_equipa)
        
        gr_banco = cursor.fetchone()[0]
        
        if posicao == 'Goalkeeper' and gr_banco <= 1:
            return False, "Deve haver pelo menos 1 guarda-redes no banco!"
        
        # Atualizar para remover do banco
        cursor.execute("""
            UPDATE FantasyChamp.Pertence
            SET benched = 0
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador)
        
        conn.commit()
        return True, "Jogador colocado em campo com sucesso!"