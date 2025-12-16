# persistence/equipa.py
from typing import NamedTuple, Dict, Optional
from pyodbc import IntegrityError
import pyodbc
from persistence.session import create_connection


class Equipa(NamedTuple):
    id: str
    nome: str
    orcamento: float
    pontuacao_total: int
    id_utilizador: str
    num_jogadores: int = 0
    valor_total_plantel: float = 0.0

class Pertence(NamedTuple):
    id_equipa: str
    id_jogador: str
    benched: bool


def criar_equipa(nome: str, id_utilizador: str) -> str:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Parâmetro de output
        equipa_id = None
        
        # Chamar a stored procedure
        cursor.execute("""
            DECLARE @EquipaID UNIQUEIDENTIFIER;
            EXEC FantasyChamp.sp_CriarEquipa 
                @Nome = ?, 
                @ID_Utilizador = ?, 
                @EquipaID = @EquipaID OUTPUT;
            SELECT @EquipaID;
        """, nome, id_utilizador)
        
        equipa_id = cursor.fetchone()[0]
        
        return str(equipa_id)


def obter_preco_jogador(id_jogador: str) -> float:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Preço 
            FROM FantasyChamp.vwJogadorPreco 
            WHERE ID = ?
        """, id_jogador)
        
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0

def verificar_orcamento_suficiente(id_equipa: str, preco_jogador: float) -> bool:
    with create_connection() as conn:
        cursor = conn.cursor()
        """ UDF: """
        cursor.execute("""
            SELECT FantasyChamp.OrcamentoSuficiente(?, ?)
        """, id_equipa, preco_jogador)
        
        return bool(cursor.fetchone()[0])
    
def obter_equipa_por_utilizador(id_utilizador: str) -> Optional[Equipa]:
    """Obtém equipa com dados completos da view"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ID, Nome, Orçamento, PontuaçãoTotal, ID_Utilizador,
                Num_Jogadores, Valor_Total_Plantel
            FROM FantasyChamp.EquipaCompleta
            WHERE ID_Utilizador = ?
        """, id_utilizador)
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return Equipa(
            id=str(row.ID),
            nome=row.Nome,
            orcamento=float(row.Orçamento),
            pontuacao_total=float(row.PontuaçãoTotal),
            id_utilizador=str(row.ID_Utilizador),
            num_jogadores=int(row.Num_Jogadores),
            valor_total_plantel=float(row.Valor_Total_Plantel) if row.Valor_Total_Plantel else 0.0
        )

def obter_jogadores_equipa(id_equipa: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ID, Nome, Posicao, Preço, jogador_imagem, 
                Estado, benched, ClubeNome, clube_imagem
            FROM FantasyChamp.JogadoresEquipa
            WHERE ID_Equipa = ?
            ORDER BY 
                CASE Posicao 
                    WHEN 'Guarda-Redes' THEN 1
                    WHEN 'Defesa' THEN 2
                    WHEN 'Médio' THEN 3
                    WHEN 'Avançado' THEN 4
                    ELSE 5
                END,
                Nome
        """, id_equipa)
        
        jogadores = []
        for row in cursor:
            jogadores.append({
                'id': str(row.ID),
                'nome': row.Nome,
                'posicao': row.Posicao,
                'preco': float(row.Preço),
                'jogador_imagem': row.jogador_imagem if row.jogador_imagem 
                          else '/static/images/Image-not-found.png',
                'estado': row.Estado,
                'benched': True if row.benched == 1 else False  
            })
        
        return jogadores


def obter_posicao_jogador(id_jogador: str) -> Optional[str]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT FantasyChamp.fn_ObterPosicaoJogador(?)
        """, id_jogador)
        
        row = cursor.fetchone()
        return row[0] if row and row[0] else None


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
        cursor.execute("""
            EXEC FantasyChamp.RemoverJogadorEquipa ?, ?
        """, id_equipa, id_jogador)
        conn.commit()


def verificar_limites_equipa(id_equipa: str) -> dict:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Usar view
        cursor.execute("""
            SELECT gr, defesa, medio, avancado, total
            FROM FantasyChamp.ContagemEquipa
            WHERE ID_Equipa = ?
        """, id_equipa)
        
        row = cursor.fetchone()
        contagem = {
            'Goalkeeper': row.gr if row else 0,
            'Defender': row.defesa if row else 0,
            'Midfielder': row.medio if row else 0,
            'Forward': row.avancado if row else 0,
            'Total': row.total if row else 0
        }
        
        # Obter orçamento
        cursor.execute("SELECT Orçamento FROM FantasyChamp.Equipa WHERE ID = ?", id_equipa)
        row = cursor.fetchone()
        orcamento_atual = float(row.Orçamento) if row else 0.0
        
        return {
            'contagem': contagem,
            'orcamento': orcamento_atual,
            'pode_adicionar_gr': contagem['Goalkeeper'] < 2,
            'pode_adicionar_defesa': contagem['Defender'] < 5,
            'pode_adicionar_medio': contagem['Midfielder'] < 5,
            'pode_adicionar_avancado': contagem['Forward'] < 3,
            'maximo_jogadores': contagem['Total'] < 15  # Exemplo: limite total de 15
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
    
def obter_detalhes_equipa_para_visualizacao(id_equipa):
    """
    Obtém todos os detalhes de uma equipa para visualização.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_ObterDetalhesEquipaParaVisualizacao 
                    @ID_Equipa = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
            """, id_equipa)
            
            # Obter informações da equipa
            equipa_info = None
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()
                if row:
                    equipa_info = dict(zip(columns, row))
            
            if not equipa_info:
                raise Exception("Equipa não encontrada")
            
            # Obter jogadores por posição
            jogadores_agrupados = {
                'gr': [],
                'defesas': [],
                'medios': [],
                'avancados': []
            }
            
            # Goalkeepers
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                for row in rows:
                    jogador = dict(zip(columns, row))
                    jogadores_agrupados['gr'].append(jogador)
            
            # Defenders
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                for row in rows:
                    jogador = dict(zip(columns, row))
                    jogadores_agrupados['defesas'].append(jogador)
            
            # Midfielders
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                for row in rows:
                    jogador = dict(zip(columns, row))
                    jogadores_agrupados['medios'].append(jogador)
            
            # Forwards
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                for row in rows:
                    jogador = dict(zip(columns, row))
                    jogadores_agrupados['avancados'].append(jogador)
            
            # Estatísticas
            estatisticas = {}
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()
                if row:
                    estatisticas = dict(zip(columns, row))
            
            return {
                'info': equipa_info,
                'jogadores': jogadores_agrupados,
                'estatisticas': estatisticas
            }
            
        except pyodbc.Error as e:
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            raise e