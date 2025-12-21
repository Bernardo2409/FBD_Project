"""
Script para popular a base de dados com dados reais da UEFA Champions League.

Este script utiliza a API Football-Data.org para obter informação sobre:
- Clubes participantes na Champions League
- Jogadores de cada clube (plantel)
- Jogos e resultados

Os dados são inseridos na base de dados FantasyChamp através de conexão ODBC.

Limitações implementadas:
- Máximo de 8 clubes
- Máximo de 15 jogadores por clube (2 GR, 5 DEF, 5 MED, 3 AVA)
- Apenas jornadas 1 a 4 processadas

APIs utilizadas:
- Football-Data.org (https://api.football-data.org/v4) - Dados de futebol
- FlagCDN (https://flagcdn.com/) - Bandeiras dos países
"""

import os
import requests
import time
import pyodbc
import random
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Carregar variáveis de ambiente do ficheiro .env
load_dotenv()

# ============================================================================
# CONFIGURAÇÃO DA API
# ============================================================================
API_KEY = os.getenv('FOOTBALL_DATA_KEY')
API_URL = "https://api.football-data.org/v4"
CHAMPIONS_LEAGUE_ID = "CL"
SEASON = 2025

# ============================================================================
# LIMITES DO DATASET
# ============================================================================
MAX_CLUBS = 8              # Número máximo de clubes a inserir
MAX_PLAYERS_PER_CLUB = 15  # Número máximo de jogadores por clube

# ============================================================================
# CONFIGURAÇÃO DA BASE DE DADOS
# ============================================================================
DB_SERVER = os.getenv('DB_SERVER', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'FantasyChamp')
DB_USER = os.getenv('DB_USER', 'sa')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')


class FootballDataClient:
    """
    Cliente para comunicação com a API Football-Data.org.
    
    Esta classe encapsula todas as chamadas HTTP à API, gerindo:
    - Autenticação via API Key
    - Rate limiting (0.6s entre pedidos)
    - Tratamento de erros e retry em caso de limite excedido
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente com a API Key.
        
        Args:
            api_key: Chave de autenticação para a API Football-Data.org
        """
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
        self.request_count = 0
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Efectua um pedido GET à API.
        
        Implementa rate limiting automático e retry em caso de erro 429.
        
        Args:
            endpoint: Caminho do endpoint (ex: "competitions/CL/teams")
            
        Returns:
            Dicionário com a resposta JSON ou None em caso de erro
        """
        try:
            url = f"{API_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                # Aguardar 0.6s entre pedidos para respeitar rate limit
                time.sleep(0.6)
                return data
            elif response.status_code == 429:
                # Rate limit excedido - aguardar 60 segundos
                print("Rate limit excedido. A aguardar 60 segundos...")
                time.sleep(60)
                return self._make_request(endpoint)
            else:
                print(f"Erro {response.status_code} no endpoint: {endpoint}")
                return None
        except Exception as e:
            print(f"Exceção ao fazer pedido: {e}")
            return None
    
    def get_teams(self, competition_code: str, season: int) -> List[Dict]:
        """
        Obtém a lista de equipas de uma competição.
        
        Args:
            competition_code: Código da competição (ex: "CL" para Champions League)
            season: Ano da época (ex: 2025)
            
        Returns:
            Lista de dicionários com dados das equipas
        """
        data = self._make_request(f"competitions/{competition_code}/teams?season={season}")
        return data.get("teams", []) if data else []
    
    def get_team_details(self, team_id: int) -> Optional[Dict]:
        """
        Obtém detalhes de uma equipa, incluindo o plantel (squad).
        
        Args:
            team_id: ID da equipa na API
            
        Returns:
            Dicionário com dados da equipa ou None
        """
        return self._make_request(f"teams/{team_id}")


class DatabaseManager:
    """
    Gestor de operações na base de dados.
    
    Esta classe encapsula todas as operações SQL, incluindo:
    - Conexão e desconexão
    - Inserção de dados (clubes, jogadores, jogos, estatísticas)
    - Limpeza de dados existentes
    - Cache de posições e estados para evitar queries repetidas
    """
    
    def __init__(self, server: str, database: str, user: str, password: str):
        """
        Inicializa o gestor com os parâmetros de conexão.
        
        Args:
            server: Endereço do servidor SQL
            database: Nome da base de dados
            user: Utilizador SQL
            password: Palavra-passe
        """
        self.conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}"
        )
        self.conn = None
        self.position_cache = {}  # Cache para evitar queries repetidas
        self.estado_cache = {}
    
    def connect(self):
        """
        Estabelece conexão com a base de dados.
        
        Returns:
            True se conexão bem sucedida, False caso contrário
        """
        try:
            self.conn = pyodbc.connect(self.conn_string)
            print("Conexão à base de dados estabelecida")
            return True
        except Exception as e:
            print(f"Falha na conexão: {e}")
            return False
    
    def close(self):
        """Fecha a conexão com a base de dados."""
        if self.conn:
            self.conn.close()
            print("Conexão fechada")
    
    def execute_query(self, query: str, params: tuple = ()):
        """
        Executa uma query SQL com parâmetros.
        
        Args:
            query: Query SQL a executar
            params: Tuplo com parâmetros para a query
            
        Returns:
            True se execução bem sucedida, False caso contrário
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro na query: {e}")
            self.conn.rollback()
            return False
    
    def fetch_one(self, query: str, params: tuple = ()):
        """
        Executa uma query e retorna o primeiro resultado.
        
        Args:
            query: Query SQL de SELECT
            params: Tuplo com parâmetros
            
        Returns:
            Primeira linha do resultado ou None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            return None
    
    def clean_game_data(self):
        """
        Remove todos os dados de jogo existentes.
        
        Limpa as tabelas na ordem correcta para respeitar
        as restrições de chave estrangeira.
        """
        print("\nA limpar dados existentes...")
        
        # Ordem importante devido às foreign keys
        queries = [
            "DELETE FROM FantasyChamp.Pontuação_Jogador",
            "DELETE FROM FantasyChamp.Pontuação_Equipa",
            "DELETE FROM FantasyChamp.Pertence",
            "DELETE FROM FantasyChamp.Participa",
            "DELETE FROM FantasyChamp.Jogo",
            "DELETE FROM FantasyChamp.Jornada",
            "DELETE FROM FantasyChamp.Jogador",
            "DELETE FROM FantasyChamp.Clube",
            "DELETE FROM FantasyChamp.Liga WHERE Nome IN ('Mundial', 'Portugal', 'Spain', 'Germany', 'United Kingdom')",
        ]
        
        for query in queries:
            self.execute_query(query)
        
        print("Limpeza concluída\n")
    
    def get_or_create_position(self, position_name: str) -> Optional[str]:
        """
        Obtém ou cria uma posição na base de dados.
        
        Utiliza cache para evitar queries repetidas.
        
        Args:
            position_name: Nome da posição (Goalkeeper, Defender, etc.)
            
        Returns:
            ID da posição ou None
        """
        if position_name in self.position_cache:
            return self.position_cache[position_name]
        
        result = self.fetch_one(
            "SELECT ID FROM FantasyChamp.Posição WHERE Posição = ?",
            (position_name,)
        )
        
        if result:
            self.position_cache[position_name] = result[0]
            return result[0]
        
        # Mapeamento de posições para IDs pré-definidos
        position_map = {
            'Goalkeeper': 'POS01',
            'Defender': 'POS02',
            'Midfielder': 'POS03',
            'Forward': 'POS04'
        }
        
        pos_id = position_map.get(position_name)
        if not pos_id:
            return None
        
        self.execute_query(
            "IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Posição WHERE ID = ?) "
            "INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES (?, ?)",
            (pos_id, pos_id, position_name)
        )
        
        self.position_cache[position_name] = pos_id
        return pos_id
    
    def get_or_create_estado(self, estado_name: str) -> Optional[str]:
        """
        Obtém ou cria um estado de jogador na base de dados.
        
        Args:
            estado_name: Nome do estado (Active, Injured, etc.)
            
        Returns:
            ID do estado ou None
        """
        if estado_name in self.estado_cache:
            return self.estado_cache[estado_name]
        
        result = self.fetch_one(
            "SELECT ID FROM FantasyChamp.Estado_Jogador WHERE Estado = ?",
            (estado_name,)
        )
        
        if result:
            self.estado_cache[estado_name] = result[0]
            return result[0]
        
        estado_id = f"STT{len(self.estado_cache) + 1:02d}"
        self.execute_query(
            "INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES (?, ?)",
            (estado_id, estado_name)
        )
        
        self.estado_cache[estado_name] = estado_id
        return estado_id

    def insert_team(self, team_data: Dict) -> bool:
        """
        Insere um clube na base de dados.
        
        Args:
            team_data: Dicionário com dados da equipa da API
            
        Returns:
            True se inserção bem sucedida
        """
        team_id = str(team_data['id'])
        name = team_data['name']
        crest = team_data.get('crest', '')
        country_code = team_data.get('area', {}).get('code', 'EU')
        
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?)
            INSERT INTO FantasyChamp.Clube (ID, Nome, ID_País, clube_imagem)
            VALUES (?, ?, ?, ?)
        """
        
        return self.execute_query(query, (team_id, team_id, name, country_code, crest))
    
    def insert_player(self, player_data: Dict, team_id: str) -> bool:
        """
        Insere um jogador na base de dados.
        
        O preço é gerado aleatoriamente entre 4.0 e 10.0 milhões.
        A foto é gerada usando UI Avatars API.
        
        Args:
            player_data: Dicionário com dados do jogador da API
            team_id: ID do clube
            
        Returns:
            True se inserção bem sucedida
        """
        player_id = str(player_data['id'])
        name = player_data['name']
        # Gerar URL de avatar baseado no nome
        photo = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=128"
        
        # Mapear posição da API para posição interna
        api_position = player_data.get('position', 'Midfield')
        position_map = {
            'Goalkeeper': 'Goalkeeper',
            'Defence': 'Defender',
            'Midfield': 'Midfielder',
            'Offence': 'Forward'
        }
        position_name = position_map.get(api_position, 'Midfielder')
        position_id = self.get_or_create_position(position_name)
        
        if not position_id:
            return False
        
        # Preço aleatório entre 4.0 e 10.0 milhões
        price = round(random.uniform(4.0, 10.0), 1)
        estado_id = self.get_or_create_estado('Active')
        if not estado_id:
            return False
        
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jogador WHERE ID = ?)
            INSERT INTO FantasyChamp.Jogador (ID, Nome, jogador_imagem, Preço, ID_Posição, ID_clube, ID_Estado_Jogador)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        return self.execute_query(
            query,
            (player_id, player_id, name, photo, price, position_id, team_id, estado_id)
        )
    
    def insert_jornada(self, jornada_id: str, numero: int, data_inicio: str, data_fim: str) -> bool:
        """
        Insere uma jornada na base de dados.
        
        Args:
            jornada_id: ID da jornada (ex: "J001")
            numero: Número da jornada
            data_inicio: Data de início no formato YYYY-MM-DD
            data_fim: Data de fim no formato YYYY-MM-DD
            
        Returns:
            True se inserção bem sucedida
        """
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = ?)
            INSERT INTO FantasyChamp.Jornada (ID, Numero, Data_Inicio, Data_Fim)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_query(query, (jornada_id, jornada_id, numero, data_inicio, data_fim))
    
    def insert_match(self, match_data: Dict, match_details: Optional[Dict] = None) -> Optional[str]:
        """
        Insere um jogo na base de dados.
        
        Apenas processa jogos das jornadas 1-4.
        
        Args:
            match_data: Dicionário com dados do jogo
            match_details: Detalhes adicionais do jogo (opcional)
            
        Returns:
            ID do jogo inserido ou None
        """
        matchday = match_data.get('matchday', 1)
        
        # Inserir apenas jornadas 1-4
        if matchday < 1 or matchday > 4:
            return None
        
        home_team = match_data['homeTeam']
        away_team = match_data['awayTeam']
        score = match_data.get('score', {}).get('fullTime', {})
        
        match_date = match_data.get('utcDate', '2025-09-01')[:10]
        jornada_id = f"J{matchday:03d}"
        
        self.insert_jornada(jornada_id, matchday, match_date, match_date)
        
        home_team_id = str(home_team['id'])
        away_team_id = str(away_team['id'])
        
        # Verificar se ambos os clubes existem
        if not self.fetch_one("SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?", (home_team_id,)):
            return None
        if not self.fetch_one("SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?", (away_team_id,)):
            return None
        
        match_id = str(uuid.uuid4())
        home_goals = score.get('home')
        away_goals = score.get('away')
        
        query = """
            INSERT INTO FantasyChamp.Jogo (ID, [Data], ID_Clube1, ID_Clube2, ID_jornada, golos_clube1, golos_clube2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        if self.execute_query(query, (match_id, match_date, home_team_id, away_team_id, jornada_id, home_goals, away_goals)):
            if match_details and home_goals is not None and away_goals is not None:
                self._process_match_statistics(match_details, jornada_id, home_team_id, away_team_id)
            return match_id
        return None
    
    def _process_match_statistics(self, match_details: Dict, jornada_id: str, home_team_id: str, away_team_id: str):
        """
        Processa estatísticas reais de um jogo a partir dos dados da API.
        
        Extrai informação sobre golos, assistências, cartões e substituições.
        """
        match_data = match_details.get('match', match_details)
        
        goals = match_data.get('goals', [])
        bookings = match_data.get('bookings', [])
        substitutions = match_data.get('substitutions', [])
        home_lineup = match_data.get('homeTeam', {}).get('lineup', [])
        away_lineup = match_data.get('awayTeam', {}).get('lineup', [])
        
        self._process_team_statistics(home_lineup, home_team_id, jornada_id, goals, bookings, substitutions, True)
        self._process_team_statistics(away_lineup, away_team_id, jornada_id, goals, bookings, substitutions, False)
    
    def _process_team_statistics(self, lineup: List[Dict], team_id: str, jornada_id: str, 
                                  goals: List[Dict], bookings: List[Dict], substitutions: List[Dict], is_home: bool):
        """
        Processa estatísticas para uma equipa num jogo.
        
        Para cada jogador no onze inicial, calcula:
        - Tempo de jogo (ajustado por substituições e expulsões)
        - Golos marcados
        - Assistências
        - Cartões amarelos e vermelhos
        - Golos sofridos (para GR e defesas)
        """
        if not lineup:
            return
        
        cursor = self.conn.cursor()
        
        for player in lineup:
            player_id = str(player.get('id'))
            
            if not self.fetch_one("SELECT 1 FROM FantasyChamp.Jogador WHERE ID = ?", (player_id,)):
                continue
            
            stats = {
                'TempoJogo': 90,
                'GolosSofridos': 0,
                'GolosMarcados': 0,
                'Assistencias': 0,
                'CartoesAmarelos': 0,
                'CartoesVermelhos': 0
            }
            
            # Contar golos marcados
            for goal in goals:
                scorer = goal.get('scorer', {})
                if scorer and str(scorer.get('id')) == player_id:
                    stats['GolosMarcados'] += 1
                
                assist = goal.get('assist')
                if assist and str(assist.get('id')) == player_id:
                    stats['Assistencias'] += 1
            
            # Contar cartões
            for booking in bookings:
                booking_player = booking.get('player', {})
                if booking_player and str(booking_player.get('id')) == player_id:
                    card_type = booking.get('card', '')
                    if card_type == 'YELLOW_CARD':
                        stats['CartoesAmarelos'] += 1
                    elif card_type == 'RED_CARD':
                        stats['CartoesVermelhos'] += 1
                        minute = booking.get('minute', 90)
                        stats['TempoJogo'] = min(stats['TempoJogo'], minute)
            
            # Verificar substituições (tempo de jogo)
            for sub in substitutions:
                player_out = sub.get('playerOut', {})
                player_in = sub.get('playerIn', {})
                minute = sub.get('minute', 0)
                
                if player_out and str(player_out.get('id')) == player_id:
                    stats['TempoJogo'] = min(stats['TempoJogo'], minute)
                elif player_in and str(player_in.get('id')) == player_id:
                    stats['TempoJogo'] = 90 - minute
            
            # Golos sofridos (apenas para GR e Defesas que jogaram 60+ min)
            position = player.get('position', '')
            if position in ['Goalkeeper', 'Defender'] and stats['TempoJogo'] >= 60:
                cursor.execute("""
                    SELECT golos_clube1, golos_clube2, ID_Clube1, ID_Clube2
                    FROM FantasyChamp.Jogo
                    WHERE ID_jornada = ? AND (ID_Clube1 = ? OR ID_Clube2 = ?)
                """, jornada_id, team_id, team_id)
                
                match_result = cursor.fetchone()
                if match_result:
                    golos_clube1, golos_clube2, clube1, clube2 = match_result
                    if clube1 == team_id:
                        stats['GolosSofridos'] = golos_clube2 if golos_clube2 else 0
                    else:
                        stats['GolosSofridos'] = golos_clube1 if golos_clube1 else 0
            
            self.insert_player_pontuacao(player_id, jornada_id, stats)
    
    def populate_player_statistics_for_matchdays(self):
        """
        Gera estatísticas realistas para todos os jogadores nas jornadas 1-4.
        
        Para cada jogo, distribui golos e assistências de forma realista:
        - Atacantes e médios têm maior probabilidade de marcar
        - Cada golo tem exactamente uma assistência
        - Guarda-redes e defesas recebem golos sofridos
        
        Returns:
            Total de registos de estatísticas gerados
        """
        print("\nA gerar estatísticas de jogadores para jornadas 1-4...")
        
        total_stats = 0
        
        for matchday in range(1, 5):
            jornada_id = f"J{matchday:03d}"
            
            if not self.fetch_one("SELECT 1 FROM FantasyChamp.Jornada WHERE ID = ?", (jornada_id,)):
                continue
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ID, ID_Clube1, ID_Clube2, golos_clube1, golos_clube2
                FROM FantasyChamp.Jogo
                WHERE ID_jornada = ?
            """, jornada_id)
            
            matches = cursor.fetchall()
            
            for match in matches:
                match_id, home_id, away_id, home_goals, away_goals = match
                
                if home_goals is None or away_goals is None:
                    continue
                
                cursor.execute("""
                    SELECT J.ID, P.Posição, J.ID_clube
                    FROM FantasyChamp.Jogador J
                    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
                    WHERE J.ID_clube IN (?, ?)
                """, home_id, away_id)
                
                team_players = cursor.fetchall()
                
                home_players = [(pid, pos) for pid, pos, club in team_players if club == home_id]
                away_players = [(pid, pos) for pid, pos, club in team_players if club == away_id]
                
                if not home_players or not away_players:
                    continue
                
                self._create_match_stats_for_team(home_players, home_goals, away_goals, jornada_id)
                self._create_match_stats_for_team(away_players, away_goals, home_goals, jornada_id)
                
                total_stats += len(home_players) + len(away_players)
        
        print(f"Total de estatísticas geradas: {total_stats}")
        return total_stats
    
    def _create_match_stats_for_team(self, players: list, goals_scored: int, goals_conceded: int, jornada_id: str):
        """
        Cria estatísticas realistas para uma equipa num jogo.
        
        Garante que:
        - Total de golos = total de assistências
        - Atacantes marcam mais golos
        - Tempo de jogo varia (titulares 80-90min, suplentes 15-30min)
        - Probabilidade realista de cartões (15% amarelo, 2% vermelho)
        """
        if not players:
            return
        
        # Selecionar 14 jogadores que participam
        num_players = min(14, len(players))
        playing = random.sample(players, num_players)
        
        if not playing:
            return
        
        # Distribuir golos entre avançados e médios
        goal_scorers = []
        if goals_scored > 0:
            attackers = [(p, pos) for p, pos in playing if pos in ['Forward', 'Midfielder']]
            if attackers:
                goal_scorers = random.choices(attackers, k=goals_scored)
            else:
                goal_scorers = random.choices(playing, k=goals_scored)
        
        # Cada golo tem 1 assistência ou nenhuma(penálti, livre, canto direto,...)
        assists = []
        for _ in range(goals_scored):
            potential_assisters = [(p, pos) for p, pos in playing if pos in ['Midfielder', 'Forward']]
            if potential_assisters:
                assists.append(random.choice(potential_assisters))
            elif playing:
                assists.append(random.choice(playing))
        
        # Criar estatísticas para cada jogador
        for player_id, position in playing:
            stats = {
                'TempoJogo': 0,
                'GolosSofridos': 0,
                'GolosMarcados': 0,
                'Assistencias': 0,
                'CartoesAmarelos': 0,
                'CartoesVermelhos': 0
            }
            
            # Tempo de jogo
            starter_idx = playing.index((player_id, position))
            if starter_idx < 11:
                stats['TempoJogo'] = random.choice([90, 90, 90, 85, 80])
            else:
                stats['TempoJogo'] = random.choice([15, 20, 25, 30])
            
            # Golos
            stats['GolosMarcados'] = sum(1 for (p, _) in goal_scorers if p == player_id)
            
            # Assistências
            stats['Assistencias'] = sum(1 for (p, _) in assists if p == player_id)
            
            # Golos sofridos (GR/Defesas)
            if position in ['Goalkeeper', 'Defender'] and stats['TempoJogo'] >= 45:
                stats['GolosSofridos'] = goals_conceded
            
            # Cartões
            if random.random() < 0.15:
                stats['CartoesAmarelos'] = 1
            if random.random() < 0.02:
                stats['CartoesVermelhos'] = 1
                stats['TempoJogo'] = min(stats['TempoJogo'], random.randint(30, 70))
            
            self.insert_player_pontuacao(player_id, jornada_id, stats)
    
    def insert_player_pontuacao(self, player_id: str, jornada_id: str, stats: Dict) -> bool:
        """
        Insere a pontuação de um jogador numa jornada.
        
        Fórmula de cálculo da pontuação:
        - +1 ponto por cada 30 minutos jogados
        - +5 pontos por golo marcado
        - +3 pontos por assistência
        - -1 ponto por cartão amarelo
        - -3 pontos por cartão vermelho
        
        Args:
            player_id: ID do jogador
            jornada_id: ID da jornada
            stats: Dicionário com estatísticas do jogador
            
        Returns:
            True se inserção bem sucedida
        """
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Jogador 
                          WHERE ID_jogador = ? AND ID_jornada = ?)
            INSERT INTO FantasyChamp.Pontuação_Jogador 
                (ID_jogador, ID_jornada, TempoJogo, GolosSofridos, GolosMarcados, 
                 Assistencias, CartoesAmarelos, CartoesVermelhos, pontuação_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Calcular pontuação total
        pontuacao = 0
        if stats['TempoJogo'] >= 30:
            pontuacao += stats['TempoJogo'] // 30
        
        pontuacao += stats['GolosMarcados'] * 5
        pontuacao += stats['Assistencias'] * 3
        pontuacao -= stats['CartoesAmarelos'] * 1
        pontuacao -= stats['CartoesVermelhos'] * 3
        
        return self.execute_query(
            query,
            (player_id, jornada_id, 
             player_id, jornada_id,
             stats['TempoJogo'], stats['GolosSofridos'], stats['GolosMarcados'],
             stats['Assistencias'], stats['CartoesAmarelos'], stats['CartoesVermelhos'],
             str(pontuacao))
        )


def main():
    """
    Função principal que orquestra todo o processo de população.
    
    Passos executados:
    1. Verificar API Key
    2. Conectar à base de dados
    3. Limpar dados existentes (opcional)
    4. Obter e inserir clubes da API
    5. Obter e inserir jogadores de cada clube
    6. Criar jogos fictícios para 4 jornadas
    7. Mostrar resumo final
    """
    print("=" * 70)
    print("População da Base de Dados - UEFA Champions League")
    print("Jornadas 1-4")
    print("=" * 70)
    
    if not API_KEY:
        print("\nERRO: FOOTBALL_DATA_KEY não encontrada no ficheiro .env")
        return
    
    api = FootballDataClient(API_KEY)
    db = DatabaseManager(DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD)
    
    if not db.connect():
        return
    
    try:
        clean = input("\nLimpar dados existentes? (s/n): ").lower()
        if clean == 's':
            db.clean_game_data()
        
        print(f"\nA obter equipas da Champions League...")
        all_teams = api.get_teams(CHAMPIONS_LEAGUE_ID, SEASON)
        print(f"Encontradas {len(all_teams)} equipas")
        
        # Limitar a 8 clubes
        teams = all_teams[:MAX_CLUBS]
        print(f"A usar {len(teams)} equipas\n")
        
        print("A inserir equipas...")
        for team in teams:
            db.insert_team(team)
        
        print(f"\nA obter jogadores...")
        total_players = 0
        
        for i, team in enumerate(teams, 1):
            team_id = team['id']
            team_name = team['name']
            
            print(f"[{i}/{len(teams)}] {team_name}")
            
            team_details = api.get_team_details(team_id)
            
            if team_details and 'squad' in team_details:
                full_squad = team_details['squad']
                
                # Distribuição: 2 GR, 5 DEF, 5 MED, 3 AVA
                goalkeepers = [p for p in full_squad if p.get('position') == 'Goalkeeper'][:2]
                defenders = [p for p in full_squad if p.get('position') == 'Defence'][:5]
                midfielders = [p for p in full_squad if p.get('position') == 'Midfield'][:5]
                forwards = [p for p in full_squad if p.get('position') == 'Offence'][:3]
                
                squad = goalkeepers + defenders + midfielders + forwards
                
                # Completar até 15 se necessário
                if len(squad) < MAX_PLAYERS_PER_CLUB:
                    remaining = [p for p in full_squad if p not in squad]
                    squad.extend(remaining[:MAX_PLAYERS_PER_CLUB - len(squad)])
                
                squad = squad[:MAX_PLAYERS_PER_CLUB]
                
                for player in squad:
                    if db.insert_player(player, str(team_id)):
                        total_players += 1
        
        print(f"\nTotal de jogadores inseridos: {total_players}")
        
        print(f"\nA criar jogos fictícios para 4 jornadas...")
        
        team_ids = [str(team['id']) for team in teams]
        matches_inserted = 0
        
        for matchday in range(1, 5):
            jornada_id = f"J{matchday:03d}"
            match_date = (datetime(2025, 9, 1) + timedelta(days=(matchday-1)*7)).strftime('%Y-%m-%d')
            
            db.insert_jornada(jornada_id, matchday, match_date, match_date)
            
            # Criar 4 jogos por jornada (8 equipas)
            shuffled_teams = team_ids.copy()
            random.shuffle(shuffled_teams)
            
            for i in range(0, len(shuffled_teams), 2):
                if i + 1 < len(shuffled_teams):
                    home_team_id = shuffled_teams[i]
                    away_team_id = shuffled_teams[i + 1]
                    
                    # Resultados aleatórios
                    home_goals = random.randint(0, 5)
                    away_goals = random.randint(0, 5)
                    
                    match_id = str(uuid.uuid4())
                    
                    query = """
                        INSERT INTO FantasyChamp.Jogo (ID, [Data], ID_Clube1, ID_Clube2, ID_jornada, golos_clube1, golos_clube2)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    if db.execute_query(query, (match_id, match_date, home_team_id, away_team_id, jornada_id, home_goals, away_goals)):
                        matches_inserted += 1
        
        print(f"Total de jogos inseridos: {matches_inserted}")
        
        # Gerar estatísticas dos jogadores
        db.populate_player_statistics_for_matchdays()
        
        # Resumo final
        print(f"\n" + "=" * 70)
        print("CONCLUÍDO")
        print("=" * 70)
        print(f"Equipas: {len(teams)}")
        print(f"Jogadores: {total_players}")
        print(f"Jogos: {matches_inserted} (4 jornadas)")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()