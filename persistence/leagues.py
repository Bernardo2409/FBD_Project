# persistence/ligas.py
from typing import NamedTuple, Optional, List
from persistence.session import create_connection
import uuid
from datetime import datetime
import pyodbc


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



# Criar liga privada

def criar_liga(
    nome: str, 
    data_inicio: str, 
    data_fim: str,
    id_tipo_liga: str = 'LT02', 
    id_criador: Optional[str] = None,
    codigo_convite: Optional[str] = None
) -> dict:
    """Versão simplificada"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            EXEC FantasyChamp.CriarLiga
                @Nome = ?,
                @Data_Inicio = ?,
                @Data_Fim = ?,
                @ID_tipoLiga = ?,
                @ID_criador = ?,
                @Codigo_Convite = ?;
        """, nome, data_inicio, data_fim, id_tipo_liga, id_criador, codigo_convite)
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': str(row.ID),
                'codigo_convite': row.Codigo_Convite,
                'sucesso': bool(row.Sucesso)
            }
        
        return {'sucesso': False, 'erro': 'Falha ao criar liga'}



# Criar liga pública (Mundial e país do utilizador)

def criar_liga_publica(nome_liga: str, id_criador: str = None) -> str:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Executar SP
        cursor.execute("""
            DECLARE @LigaID UNIQUEIDENTIFIER;
            EXEC FantasyChamp.CriarLigaPublica 
                @Nome = ?,
                @ID_criador = ?,
                @LigaID = @LigaID OUTPUT;
            SELECT @LigaID;
        """, nome_liga, id_criador)
        
        liga_id = cursor.fetchone()[0]
        conn.commit()
        
        return str(liga_id)



# Obter tipos de liga

def obter_tipos_liga() -> List[TipoLiga]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Tipo
            FROM FantasyChamp.Tipo_Liga
            ORDER BY ID
        """)

        return [TipoLiga(row.ID, row.Tipo) for row in cursor]



# Obter ligas onde o utilizar participa

def obter_ligas_por_utilizador(id_utilizador: str) -> List[Liga]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID, Nome, Data_Inicio, Data_Fim,
                   ID_tipoLiga, ID_criador, Código_Convite
            FROM FantasyChamp.LigasDoUtilizador
            WHERE ID_Utilizador = ?
        """, id_utilizador)

        return [
            Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim,
                 row.ID_tipoLiga, row.ID_criador, row.Código_Convite)
            for row in cursor
        ]


# Obter liga por ID

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



# Obter liga pelo nome

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



# User junta-se automaticamente a uma liga

def juntar_liga_automatico(id_utilizador: str, liga_id: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC FantasyChamp.JuntarLigaAutomatico ?, ?
        """, id_utilizador, liga_id)
        conn.commit()


# Juntar a liga manual

def juntar_liga(id_utilizador: str, id_liga: str, codigo: Optional[str]) -> bool:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DECLARE @Resultado BIT;
            EXEC FantasyChamp.JuntarLiga 
                @ID_Utilizador = ?,
                @ID_Liga = ?,
                @Codigo = ?,
                @Resultado = @Resultado OUTPUT;
            SELECT @Resultado;
        """, id_utilizador, id_liga, codigo)
        
        resultado = cursor.fetchone()[0]
        conn.commit()
        
        return bool(resultado)


# Obter participantes de uma liga

def obter_participantes_liga(id_liga):

    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                nome,
                equipa,
                id_equipa
            FROM FantasyChamp.ParticipantesLiga
            WHERE ID_Liga = ?
            ORDER BY nome
        """, id_liga)
        
        return [
            {
                'nome': row.nome,
                'equipa': row.equipa,
                'id_equipa': row.id_equipa
            }
            for row in cursor.fetchall()
        ]




# Ligas públicas visíveis para o utilizador
# Mundial + Liga do país do user

def obter_ligas_publicas_para_utilizador(user_country: str, id_user: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            EXEC FantasyChamp.ObterLigasPublicasParaUtilizador ?, ?
        """, user_country, id_user)
        
        return [
            Liga(row.ID, row.Nome, row.Data_Inicio, row.Data_Fim,
                 row.ID_tipoLiga, row.ID_criador,
                 row.Código_Convite, row.PrimeiroNome)
            for row in cursor.fetchall()
        ]



# Obter ID da liga a partir do código de convite

def obter_liga_id_por_codigo(codigo: str) -> Optional[str]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID FROM FantasyChamp.Liga
            WHERE Código_Convite = ?
        """, codigo)
        row = cursor.fetchone()
        return row.ID if row else None



# Abandonar liga

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
            EXEC FantasyChamp.AbandonarLiga ?, ?
        """, id_utilizador, id_liga)
        
        conn.commit()
        return True

# Obter Ranking

def obter_ranking_liga(id_liga, id_jornada=None):

    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC ObterRankingLigaComEquipas 
                    @ID_Liga = ?,
                    @ID_Jornada = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
            """, id_liga, id_jornada)
            
            # Obter resultados
            ranking = []
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    equipa = type('EquipaRanking', (), {
                        'posicao': row.posicao,
                        'nome_utilizador': row.nome_utilizador,
                        'nome_equipa': row.nome_equipa,
                        'pontuacao': row.pontuacao,
                        'pontuacao_acumulada': row.pontuacao_acumulada,
                        'id_equipa': row.id_equipa,
                        'id_utilizador': row.id_utilizador
                    })
                    ranking.append(equipa)
            
            return ranking
            
        except pyodbc.Error as e:
            print(f"Erro ao obter ranking da liga: {e}")


# Obter Jornadas Disponiveis

def obter_jornadas_disponiveis():

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ID_jornada
            FROM FantasyChamp.Jogo
            ORDER BY ID_jornada
        """)
        
        return [row.ID_jornada for row in cursor.fetchall()]


# Historico equipa liga

def obter_historico_equipa_liga(id_liga: str, id_equipa: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ID_jornada,
                pontuação_jornada,
                pontuação_acumulada
            FROM FantasyChamp.HistoricoEquipasLiga
            WHERE ID_Liga = ? AND ID_Equipa = ?
            ORDER BY ID_jornada
        """, id_liga, id_equipa)
        
        return [
            {
                'jornada': row.ID_jornada,
                'pontos_jornada': row.pontuação_jornada,
                'pontos_acumulados': row.pontuação_acumulada
            }
            for row in cursor.fetchall()
        ]

# Verificar participação na liga

def verificar_participacao_liga(id_utilizador, id_liga):
    """
    Verifica se um utilizador participa numa liga.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 1 
                FROM FantasyChamp.Participa 
                WHERE ID_Utilizador = ? AND ID_Liga = ?
            """, id_utilizador, id_liga)
            
            return cursor.fetchone() is not None
            
        except pyodbc.Error as e:
            print(f"Erro ao verificar participação na liga: {e}")
            return False