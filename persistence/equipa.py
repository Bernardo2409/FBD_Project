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
    
    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            
            # Executar stored procedure
            cursor.execute("""
                DECLARE @Sucesso BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_TrocarJogadorBancoCampo 
                    @ID_Equipa = ?,
                    @ID_Jogador_Banco = ?,
                    @ID_Jogador_Campo = ?,
                    @Sucesso = @Sucesso OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Sucesso AS Sucesso, @Mensagem AS Mensagem;
            """, id_equipa, id_jogador_banco, id_jogador_campo)
            
            result = cursor.fetchone()
            
            if result:
                sucesso = bool(result.Sucesso)
                
                mensagem = result.Mensagem
                
                if sucesso:
                    conn.commit()
                
                return sucesso, mensagem
            else:
                return False, "Erro: Stored procedure não retornou resultado"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Erro ao executar troca: {str(e)}"
                
    except pyodbc.Error as e:
        return False, f"Erro de banco de dados: {str(e)}"
    except Exception as e:
        return False, f"Erro: {str(e)}"


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