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


def contar_jogadores_por_posicao(id_equipa: str, apenas_campo: bool = False, apenas_banco: bool = False):
    """Contar jogadores por posição (no campo, no banco, ou total)"""
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
        elif apenas_banco:
            query += " AND PE.benched = 1"
        
        query += " GROUP BY P.Posição"
        
        cursor.execute(query, id_equipa)
        
        contagem = {'Goalkeeper': 0, 'Defender': 0, 'Midfielder': 0, 'Forward': 0}
        for row in cursor:
            contagem[row.Posição] = row.count
        
        return contagem


import pyodbc

def adicionar_jogador_equipa(id_equipa: str, id_jogador: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Executar stored procedure
            cursor.execute("""
                DECLARE @Resultado INT, @Mensagem NVARCHAR(200);
                
                EXEC sp_AdicionarJogadorEquipa 
                    @ID_Equipa = ?, 
                    @ID_Jogador = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Resultado, @Mensagem;
            """, id_equipa, id_jogador)
            
            row = cursor.fetchone()
            
            if row:
                resultado = row[0]
                mensagem = row[1]
                
                if resultado == 0:
                    raise Exception(mensagem)
                else:
                    conn.commit()
                    return mensagem
            else:
                raise Exception("Erro: Nenhum resultado retornado da stored procedure")
                
        except pyodbc.Error as e:
            conn.rollback()
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise e


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


def trocar_jogador_banco_campo(id_equipa: str, id_jogador_banco: str, id_jogador_campo: str) -> tuple[bool, str]:
    """
    Troca um jogador do banco com um jogador do campo.
    Retorna (sucesso, mensagem)
    """
    import logging
    logging.basicConfig(level=logging.DEBUG)
    with create_connection() as conn:
        cursor = conn.cursor()
        logging.debug(f"Troca: equipa={id_equipa}, banco={id_jogador_banco}, campo={id_jogador_campo}")
        # Verificar se o jogador do banco está realmente no banco
        cursor.execute("""
            SELECT benched FROM FantasyChamp.Pertence
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador_banco)
        row_banco = cursor.fetchone()
        logging.debug(f"row_banco={row_banco}")
        if not row_banco or row_banco.benched != 1:
            return False, "O jogador selecionado não está no banco!"
        # Verificar se o jogador do campo está realmente em campo
        cursor.execute("""
            SELECT benched FROM FantasyChamp.Pertence
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador_campo)
        row_campo = cursor.fetchone()
        logging.debug(f"row_campo={row_campo}")
        if not row_campo or row_campo.benched != 0:
            return False, "O jogador selecionado não está em campo!"
        # Obter posições dos jogadores
        posicao_banco = obter_posicao_jogador(id_jogador_banco)
        posicao_campo = obter_posicao_jogador(id_jogador_campo)
        logging.debug(f"posicao_banco={posicao_banco}, posicao_campo={posicao_campo}")
        # Verificar se são da mesma posição
        if posicao_banco != posicao_campo:
            return False, f"Não podes trocar {posicao_banco} com {posicao_campo}! Devem ser da mesma posição."
        # Contar jogadores por posição
        contagem_campo = contar_jogadores_por_posicao(id_equipa, apenas_campo=True)
        contagem_banco = contar_jogadores_por_posicao(id_equipa, apenas_banco=True)
        logging.debug(f"contagem_campo={contagem_campo}, contagem_banco={contagem_banco}")
        # VALIDAÇÃO 1: Não pode tirar o único GR do banco (mas permite se houver outro GR no banco)
        if posicao_banco == 'Goalkeeper' and contagem_banco['Goalkeeper'] <= 1:
            # Permite se houver pelo menos 1 GR em campo e 1 no banco
            if contagem_campo['Goalkeeper'] >= 1:
                pass
            else:
                return False, "Deve haver pelo menos 1 guarda-redes no banco!"
        # VALIDAÇÃO 2: Não pode tirar o único avançado do campo (mas permite se houver outro avançado em campo)
        if posicao_campo == 'Forward' and contagem_campo['Forward'] <= 1:
            if contagem_banco['Forward'] >= 1:
                pass
            else:
                return False, "Deve haver pelo menos 1 avançado em campo!"
        # VALIDAÇÃO 3: Não pode tirar o único GR do campo (mas permite se houver outro GR em campo)
        if posicao_campo == 'Goalkeeper' and contagem_campo['Goalkeeper'] <= 1:
            if contagem_banco['Goalkeeper'] >= 1:
                pass
            else:
                return False, "Deve haver pelo menos 1 guarda-redes em campo!"
        # Fazer a troca atomicamente
        cursor.execute("""
            UPDATE FantasyChamp.Pertence
            SET benched = 0
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador_banco)
        cursor.execute("""
            UPDATE FantasyChamp.Pertence
            SET benched = 1
            WHERE ID_Equipa = ? AND ID_Jogador = ?
        """, id_equipa, id_jogador_campo)
        conn.commit()
        logging.debug("Troca realizada com sucesso!")
        return True, "Troca realizada com sucesso!"


def obter_jogadores_banco_por_posicao(id_equipa: str, posicao: str):
    """Obter jogadores do banco de uma determinada posição"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, J.Preço, J.jogador_imagem, E.Estado
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            WHERE PE.ID_Equipa = ? AND PE.benched = 1 AND P.Posição = ?
        """, id_equipa, posicao)
        
        jogadores = []
        for row in cursor:
            jogadores.append({
                'id': row.ID,
                'nome': row.Nome,
                'preco': row.Preço,
                'jogador_imagem': row.jogador_imagem if row.jogador_imagem 
                          else '/static/images/Image-not-found.png',
                'estado': row.Estado
            })
        
        return jogadores