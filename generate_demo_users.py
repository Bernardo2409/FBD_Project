"""
Script para gerar 5 utilizadores de demonstração com equipas completas e pontuações.

Este script:
1. Cria 5 utilizadores demo (John, Maria, Pedro, Ana, Carlos)
2. Cria uma equipa fantasy para cada utilizador
3. Atribui 15 jogadores a cada equipa respeitando:
   - Distribuição posicional: 2 GR, 5 DEF, 5 MID, 3 FWD
   - Limite de orçamento (100M)
   - Máximo 3 jogadores do mesmo clube
4. Calcula pontuações para as jornadas 1-4

Modo de uso:
    python generate_demo_users.py
"""

import pyodbc
import os
import uuid
import random
from dotenv import load_dotenv
from typing import Optional, List, Dict, Tuple

# Carregar variáveis de ambiente
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DA BASE DE DADOS
# ============================================================================
DB_SERVER = os.getenv('DB_SERVER', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'FantasyChamp')
DB_USER = os.getenv('DB_USER', 'sa')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# ============================================================================
# DADOS DOS UTILIZADORES DEMO
# ============================================================================
DEMO_USERS = [
    {
        'primeiro_nome': 'John',
        'apelido': 'Smith',
        'email': 'john.smith@demo.com',
        'senha': 'demo123',
        'pais': 'United Kingdom',
        'nacionalidade': 'British',
        'data_nascimento': '1995-03-15',
        'equipa_nome': 'Smith FC'
    },
    {
        'primeiro_nome': 'Maria',
        'apelido': 'Garcia',
        'email': 'maria.garcia@demo.com',
        'senha': 'demo123',
        'pais': 'Spain',
        'nacionalidade': 'Spanish',
        'data_nascimento': '1990-07-22',
        'equipa_nome': 'Garcia United'
    },
    {
        'primeiro_nome': 'Pedro',
        'apelido': 'Santos',
        'email': 'pedro.santos@demo.com',
        'senha': 'demo123',
        'pais': 'Portugal',
        'nacionalidade': 'Portuguese',
        'data_nascimento': '1992-11-08',
        'equipa_nome': 'Santos XI'
    },
    {
        'primeiro_nome': 'Ana',
        'apelido': 'Müller',
        'email': 'ana.muller@demo.com',
        'senha': 'demo123',
        'pais': 'Germany',
        'nacionalidade': 'German',
        'data_nascimento': '1998-01-30',
        'equipa_nome': 'Müller Stars'
    },
    {
        'primeiro_nome': 'Carlos',
        'apelido': 'Rossi',
        'email': 'carlos.rossi@demo.com',
        'senha': 'demo123',
        'pais': 'Italy',
        'nacionalidade': 'Italian',
        'data_nascimento': '1988-09-12',
        'equipa_nome': 'Rossi Dream Team'
    }
]


class DemoDataGenerator:
    """
    Gerador de dados de demonstração para o Fantasy Champions League.
    """
    
    def __init__(self, server: str, database: str, user: str, password: str):
        self.conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}"
        )
        self.conn = None
    
    def connect(self) -> bool:
        """Estabelece conexão com a base de dados."""
        try:
            self.conn = pyodbc.connect(self.conn_string)
            print("✓ Conexão à base de dados estabelecida")
            return True
        except Exception as e:
            print(f"✗ Falha na conexão: {e}")
            return False
    
    def close(self):
        """Fecha a conexão."""
        if self.conn:
            self.conn.close()
            print("✓ Conexão fechada")
    
    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Executa uma query SQL."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Erro na query: {e}")
            self.conn.rollback()
            return False
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Retorna o primeiro resultado de uma query."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List:
        """Retorna todos os resultados de uma query."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"  ✗ Erro: {e}")
            return []
    
    def clean_demo_data(self):
        """Remove dados de demonstração existentes."""
        print("\n🗑️  A limpar dados de demonstração anteriores...")
        
        demo_emails = [u['email'] for u in DEMO_USERS]
        placeholders = ','.join(['?' for _ in demo_emails])
        
        # Obter IDs dos utilizadores demo
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT ID FROM FantasyChamp.Utilizador 
            WHERE Email IN ({placeholders})
        """, demo_emails)
        user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            print("  Nenhum utilizador demo encontrado para limpar")
            return
        
        user_placeholders = ','.join(['?' for _ in user_ids])
        
        # Obter IDs das equipas dos utilizadores demo
        cursor.execute(f"""
            SELECT ID FROM FantasyChamp.Equipa 
            WHERE ID_utilizador IN ({user_placeholders})
        """, user_ids)
        team_ids = [row[0] for row in cursor.fetchall()]
        
        if team_ids:
            team_placeholders = ','.join(['?' for _ in team_ids])
            
            # Limpar pontuações das equipas
            self.execute_query(f"""
                DELETE FROM FantasyChamp.Pontuação_Equipa 
                WHERE ID_Equipa IN ({team_placeholders})
            """, team_ids)
            
            # Limpar jogadores das equipas
            self.execute_query(f"""
                DELETE FROM FantasyChamp.Pertence 
                WHERE ID_Equipa IN ({team_placeholders})
            """, team_ids)
            
            # Limpar equipas
            self.execute_query(f"""
                DELETE FROM FantasyChamp.Equipa 
                WHERE ID IN ({team_placeholders})
            """, team_ids)
        
        # Limpar participações em ligas
        self.execute_query(f"""
            DELETE FROM FantasyChamp.Participa 
            WHERE ID_Utilizador IN ({user_placeholders})
        """, user_ids)
        
        # Limpar utilizadores
        self.execute_query(f"""
            DELETE FROM FantasyChamp.Utilizador 
            WHERE ID IN ({user_placeholders})
        """, user_ids)
        
        print(f"  ✓ Removidos {len(user_ids)} utilizadores demo e dados associados")
    
    def create_user(self, user_data: Dict) -> Optional[str]:
        """
        Cria um utilizador usando a stored procedure sp_CriarUtilizadorComLigas.
        
        Returns:
            ID do utilizador ou None
        """
        try:
            cursor = self.conn.cursor()
            
            # Verificar se email já existe
            existing = self.fetch_one(
                "SELECT ID FROM FantasyChamp.Utilizador WHERE Email = ?",
                (user_data['email'],)
            )
            if existing:
                print(f"  ⚠️ Utilizador {user_data['email']} já existe")
                return str(existing[0])
            
            # Criar utilizador diretamente (mais simples para demo)
            user_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO FantasyChamp.Utilizador 
                (ID, PrimeiroNome, Apelido, Email, Senha, País, Nacionalidade, DataDeNascimento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                user_id,
                user_data['primeiro_nome'],
                user_data['apelido'],
                user_data['email'],
                user_data['senha'],
                user_data['pais'],
                user_data['nacionalidade'],
                user_data['data_nascimento']
            ))
            self.conn.commit()
            
            return user_id
            
        except Exception as e:
            print(f"  ✗ Erro ao criar utilizador: {e}")
            self.conn.rollback()
            return None
    
    def create_team(self, user_id: str, team_name: str) -> Optional[str]:
        """
        Cria uma equipa para um utilizador.
        
        Returns:
            ID da equipa ou None
        """
        try:
            team_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO FantasyChamp.Equipa (ID, Nome, Orçamento, PontuaçãoTotal, ID_utilizador)
                VALUES (?, ?, 100.00, 0, ?)
            """
            
            cursor = self.conn.cursor()
            cursor.execute(query, (team_id, team_name, user_id))
            self.conn.commit()
            
            return team_id
            
        except Exception as e:
            print(f"  ✗ Erro ao criar equipa: {e}")
            self.conn.rollback()
            return None
    
    def get_available_players(self) -> Dict[str, List[Tuple]]:
        """
        Obtém todos os jogadores disponíveis agrupados por posição.
        
        Returns:
            Dicionário com listas de jogadores por posição
        """
        query = """
            SELECT J.ID, J.Nome, J.Preço, P.Posição, J.ID_clube
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            ORDER BY P.Posição, J.Preço DESC
        """
        
        players = self.fetch_all(query)
        
        result = {
            'Goalkeeper': [],
            'Defender': [],
            'Midfielder': [],
            'Forward': []
        }
        
        for player in players:
            position = player[3]
            if position in result:
                result[position].append({
                    'id': player[0],
                    'name': player[1],
                    'price': float(player[2]),
                    'club_id': player[4]
                })
        
        return result
    
    def select_team_players(self, available_players: Dict, budget: float = 100.0) -> List[Dict]:
        """
        Seleciona 15 jogadores respeitando as regras do jogo:
        - 2 GR (1 campo, 1 banco)
        - 5 DEF (4 campo, 1 banco)
        - 5 MID (4 campo, 1 banco)
        - 3 FWD (2 campo, 1 banco)
        - Máximo 3 jogadores do mesmo clube
        - Dentro do orçamento
        
        Returns:
            Lista de jogadores selecionados
        """
        selected = []
        total_cost = 0.0
        club_counts = {}
        
        # Requisitos por posição
        requirements = {
            'Goalkeeper': 2,
            'Defender': 5,
            'Midfielder': 5,
            'Forward': 3
        }
        
        for position, count in requirements.items():
            players = available_players.get(position, [])
            if not players:
                continue
            
            # Embaralhar jogadores para variedade
            random.shuffle(players)
            
            selected_count = 0
            for player in players:
                if selected_count >= count:
                    break
                
                # Verificar limite de jogadores por clube
                club_id = player['club_id']
                if club_counts.get(club_id, 0) >= 3:
                    continue
                
                # Verificar orçamento
                if total_cost + player['price'] > budget:
                    continue
                
                # Adicionar jogador
                selected.append(player)
                total_cost += player['price']
                club_counts[club_id] = club_counts.get(club_id, 0) + 1
                selected_count += 1
        
        return selected
    
    def add_player_to_team(self, team_id: str, player_id: str, benched: bool) -> bool:
        """
        Adiciona um jogador a uma equipa.
        """
        try:
            # Obter preço do jogador
            player = self.fetch_one(
                "SELECT Preço FROM FantasyChamp.Jogador WHERE ID = ?",
                (player_id,)
            )
            if not player:
                return False
            
            price = float(player[0])
            
            # Inserir relação Pertence
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO FantasyChamp.Pertence (ID_Equipa, ID_Jogador, benched)
                VALUES (?, ?, ?)
            """, (team_id, player_id, 1 if benched else 0))
            
            # Atualizar orçamento
            cursor.execute("""
                UPDATE FantasyChamp.Equipa
                SET Orçamento = Orçamento - ?
                WHERE ID = ?
            """, (price, team_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"  ✗ Erro ao adicionar jogador: {e}")
            self.conn.rollback()
            return False
    
    def populate_team(self, team_id: str, players: List[Dict]) -> int:
        """
        Popula uma equipa com os jogadores selecionados.
        
        Distribui jogadores entre campo e banco:
        - Campo: 1 GR, 4 DEF, 4 MID, 2 FWD (11 jogadores)
        - Banco: 1 GR, 1 DEF, 1 MID, 1 FWD (4 jogadores)
        
        Returns:
            Número de jogadores adicionados
        """
        # Agrupar por posição
        by_position = {
            'Goalkeeper': [],
            'Defender': [],
            'Midfielder': [],
            'Forward': []
        }
        
        for player in players:
            # Obter posição do jogador
            result = self.fetch_one("""
                SELECT P.Posição FROM FantasyChamp.Jogador J
                JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
                WHERE J.ID = ?
            """, (player['id'],))
            
            if result:
                position = result[0]
                if position in by_position:
                    by_position[position].append(player)
        
        # Limites de campo por posição
        field_limits = {
            'Goalkeeper': 1,
            'Defender': 4,
            'Midfielder': 4,
            'Forward': 2
        }
        
        added = 0
        for position, pos_players in by_position.items():
            field_count = 0
            field_limit = field_limits.get(position, 0)
            
            for player in pos_players:
                benched = field_count >= field_limit
                if self.add_player_to_team(team_id, player['id'], benched):
                    added += 1
                    if not benched:
                        field_count += 1
        
        return added
    
    def calculate_team_scores(self, team_id: str) -> Dict[str, int]:
        """
        Calcula as pontuações da equipa para as jornadas 1-4.
        
        Returns:
            Dicionário com pontuação por jornada
        """
        scores = {}
        accumulated = 0
        
        for matchday in range(1, 5):
            jornada_id = f"J{matchday:03d}"
            
            # Verificar se a jornada existe
            if not self.fetch_one("SELECT 1 FROM FantasyChamp.Jornada WHERE ID = ?", (jornada_id,)):
                continue
            
            # Calcular pontuação da jornada
            # Soma das pontuações dos jogadores titulares (em campo)
            result = self.fetch_one("""
                SELECT ISNULL(SUM(CAST(PJ.pontuação_total AS INT)), 0)
                FROM FantasyChamp.Pertence PE
                JOIN FantasyChamp.Pontuação_Jogador PJ ON PE.ID_Jogador = PJ.ID_jogador
                WHERE PE.ID_Equipa = ?
                  AND PE.benched = 0
                  AND PJ.ID_jornada = ?
            """, (team_id, jornada_id))
            
            round_score = result[0] if result else 0
            accumulated += round_score
            scores[jornada_id] = round_score
            
            # Inserir/atualizar pontuação na tabela
            existing = self.fetch_one("""
                SELECT 1 FROM FantasyChamp.Pontuação_Equipa 
                WHERE ID_Equipa = ? AND ID_jornada = ?
            """, (team_id, jornada_id))
            
            if existing:
                self.execute_query("""
                    UPDATE FantasyChamp.Pontuação_Equipa
                    SET pontuação_jornada = ?, pontuação_acumulada = ?
                    WHERE ID_Equipa = ? AND ID_jornada = ?
                """, (round_score, accumulated, team_id, jornada_id))
            else:
                self.execute_query("""
                    INSERT INTO FantasyChamp.Pontuação_Equipa 
                    (ID_Equipa, ID_jornada, pontuação_jornada, pontuação_acumulada)
                    VALUES (?, ?, ?, ?)
                """, (team_id, jornada_id, round_score, accumulated))
            
            # Atualizar pontuação total na tabela Equipa
            self.execute_query("""
                UPDATE FantasyChamp.Equipa
                SET PontuaçãoTotal = ?
                WHERE ID = ?
            """, (accumulated, team_id))
        
        return scores
    
    def generate_demo_data(self):
        """
        Função principal que gera todos os dados de demonstração.
        """
        print("\n" + "=" * 70)
        print("🎮 GERAÇÃO DE DADOS DE DEMONSTRAÇÃO")
        print("    Fantasy Champions League")
        print("=" * 70)
        
        # Limpar dados anteriores
        self.clean_demo_data()
        
        # Obter jogadores disponíveis
        print("\n📋 A obter jogadores disponíveis...")
        available_players = self.get_available_players()
        
        total_players = sum(len(p) for p in available_players.values())
        print(f"  ✓ {total_players} jogadores disponíveis")
        for pos, players in available_players.items():
            print(f"    - {pos}: {len(players)}")
        
        if total_players < 75:  # 15 jogadores * 5 utilizadores
            print("  ⚠️ Aviso: Poucos jogadores disponíveis. Execute populate_db.py primeiro.")
        
        # Criar utilizadores e equipas
        print("\n👥 A criar utilizadores e equipas...")
        
        created_users = []
        
        for i, user_data in enumerate(DEMO_USERS, 1):
            print(f"\n[{i}/5] {user_data['primeiro_nome']} {user_data['apelido']}")
            
            # Criar utilizador
            user_id = self.create_user(user_data)
            if not user_id:
                print(f"  ✗ Falha ao criar utilizador")
                continue
            print(f"  ✓ Utilizador criado: {user_id[:8]}...")
            
            # Criar equipa
            team_id = self.create_team(user_id, user_data['equipa_nome'])
            if not team_id:
                print(f"  ✗ Falha ao criar equipa")
                continue
            print(f"  ✓ Equipa '{user_data['equipa_nome']}' criada")
            
            # Selecionar e adicionar jogadores
            players = self.select_team_players(available_players)
            if len(players) < 15:
                print(f"  ⚠️ Apenas {len(players)} jogadores selecionados (esperado: 15)")
            
            added = self.populate_team(team_id, players)
            print(f"  ✓ {added} jogadores adicionados à equipa")
            
            # Calcular pontuações
            scores = self.calculate_team_scores(team_id)
            total = sum(scores.values())
            print(f"  ✓ Pontuações calculadas:")
            for jornada, score in scores.items():
                print(f"    - {jornada}: {score} pontos")
            print(f"    Total: {total} pontos")
            
            created_users.append({
                'user_id': user_id,
                'team_id': team_id,
                'name': f"{user_data['primeiro_nome']} {user_data['apelido']}",
                'team_name': user_data['equipa_nome'],
                'email': user_data['email'],
                'total_score': total
            })
        
        # Resumo final
        print("\n" + "=" * 70)
        print("✅ RESUMO")
        print("=" * 70)
        print(f"Utilizadores criados: {len(created_users)}")
        
        if created_users:
            print("\n📊 Ranking por pontuação:")
            sorted_users = sorted(created_users, key=lambda x: x['total_score'], reverse=True)
            for i, user in enumerate(sorted_users, 1):
                print(f"  {i}. {user['team_name']} ({user['name']}): {user['total_score']} pts")
            
            print("\n🔑 Credenciais de login:")
            for user_data in DEMO_USERS:
                print(f"  Email: {user_data['email']} | Senha: {user_data['senha']}")
        
        print("=" * 70)


def main():
    """Função principal."""
    generator = DemoDataGenerator(DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD)
    
    if not generator.connect():
        return
    
    try:
        generator.generate_demo_data()
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.close()


if __name__ == "__main__":
    main()
