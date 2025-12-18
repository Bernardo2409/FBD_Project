"""
Script to populate database with real UEFA Champions League data
FIXED VERSION - Only Matchdays 1-4 with REALISTIC data
"""

import os
import requests
import time
import pyodbc
from dotenv import load_dotenv
from typing import List, Dict, Optional
import random

load_dotenv()

API_KEY = os.getenv('FOOTBALL_DATA_KEY')
API_URL = "https://api.football-data.org/v4"
CHAMPIONS_LEAGUE_ID = "CL"
SEASON = 2025

# Database Configuration
DB_SERVER = os.getenv('DB_SERVER', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'FantasyChamp')
DB_USER = os.getenv('DB_USER', 'sa')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')


class FootballDataClient:
    """Client for Football-Data.org API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
        self.request_count = 0
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        try:
            url = f"{API_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers)
            self.request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Request {self.request_count}: {endpoint}")
                time.sleep(0.6)
                return data
            elif response.status_code == 429:
                print(f"⚠️  Rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint)
            else:
                print(f"✗ Error {response.status_code}: {endpoint}")
                return None
        except Exception as e:
            print(f"✗ Exception: {e}")
            return None
    
    def get_teams(self, competition_code: str, season: int) -> List[Dict]:
        data = self._make_request(f"competitions/{competition_code}/teams?season={season}")
        return data.get("teams", []) if data else []
    
    def get_team_details(self, team_id: int) -> Optional[Dict]:
        return self._make_request(f"teams/{team_id}")
    
    def get_matches(self, competition_code: str, season: int) -> List[Dict]:
        data = self._make_request(f"competitions/{competition_code}/matches?season={season}")
        return data.get("matches", []) if data else []
    
    def get_match_details(self, match_id: int) -> Optional[Dict]:
        """Get detailed match info including lineup, goals, assists, bookings"""
        return self._make_request(f"matches/{match_id}")


class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, server: str, database: str, user: str, password: str):
        self.conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password}"
        )
        self.conn = None
        self.position_cache = {}
        self.estado_cache = {}
    
    def connect(self):
        try:
            self.conn = pyodbc.connect(self.conn_string)
            print("✓ Connected to database")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
    
    def execute_query(self, query: str, params: tuple = ()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"✗ Query failed: {e}")
            self.conn.rollback()
            return False
    
    def fetch_one(self, query: str, params: tuple = ()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            return None
    
    def clean_game_data(self):
        """Clean existing game data"""
        print("\n🧹 Cleaning existing game data...")
        
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
            if self.execute_query(query):
                table_name = query.split('FROM')[1].strip().split()[0] if 'FROM' in query else 'Liga'
                print(f"  ✓ Cleared {table_name}")
        
        print("✓ Data cleanup complete\n")
    
    def get_or_create_position(self, position_name: str) -> Optional[str]:
        if position_name in self.position_cache:
            return self.position_cache[position_name]
        
        result = self.fetch_one(
            "SELECT ID FROM FantasyChamp.Posição WHERE Posição = ?",
            (position_name,)
        )
        
        if result:
            self.position_cache[position_name] = result[0]
            return result[0]
        
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
            "IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Posição WHERE ID = ?) INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES (?, ?)",
            (pos_id, pos_id, position_name)
        )
        
        self.position_cache[position_name] = pos_id
        return pos_id
    
    def get_or_create_estado(self, estado_name: str) -> Optional[str]:
        if estado_name in self.estado_cache:
            return self.estado_cache[estado_name]
        
        result = self.fetch_one(
            "SELECT ID FROM FantasyChamp.Estado_Jogador WHERE Estado = ?",
            (estado_name,)
        )
        
        if result:
            self.estado_cache[estado_name] = result[0]
            return result[0]
        
        estado_id = f"EST{len(self.estado_cache) + 1:02d}"
        self.execute_query(
            "INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES (?, ?)",
            (estado_id, estado_name)
        )
        
        self.estado_cache[estado_name] = estado_id
        return estado_id
    

    def insert_team(self, team_data: Dict) -> bool:
        team_id = str(team_data['id'])
        name = team_data['name']
        crest = team_data.get('crest', '')
        
        country_code = team_data.get('area', {}).get('code', 'EU')
        
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?)
            INSERT INTO FantasyChamp.Clube (ID, Nome, ID_País, clube_imagem)
            VALUES (?, ?, ?, ?)
        """
        
        if self.execute_query(query, (team_id, team_id, name, country_code, crest)):
            print(f"  ✓ Team: {name}")
            return True
        return False
    
    def insert_player(self, player_data: Dict, team_id: str) -> bool:
        player_id = str(player_data['id'])
        name = player_data['name']
        photo = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=128"
        
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
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = ?)
            INSERT INTO FantasyChamp.Jornada (ID, Numero, Data_Inicio, Data_Fim)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_query(query, (jornada_id, jornada_id, numero, data_inicio, data_fim))
    
    def insert_match(self, match_data: Dict, match_details: Optional[Dict] = None) -> Optional[str]:
        """Insert match and return match_id for later processing - ONLY matchdays 1-4"""
        matchday = match_data.get('matchday', 1)
        
        # 🔥 CRITICAL: Skip anything not matchday 1-4
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
        
        if not self.fetch_one("SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?", (home_team_id,)):
            return None
        if not self.fetch_one("SELECT 1 FROM FantasyChamp.Clube WHERE ID = ?", (away_team_id,)):
            return None
        
        import uuid
        match_id = str(uuid.uuid4())
        
        home_goals = score.get('home')
        away_goals = score.get('away')
        
        query = """
            INSERT INTO FantasyChamp.Jogo (ID, [Data], ID_Clube1, ID_Clube2, ID_jornada, golos_clube1, golos_clube2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        if self.execute_query(query, (match_id, match_date, home_team_id, away_team_id, jornada_id, home_goals, away_goals)):
            # Process real player statistics if details available
            if match_details and home_goals is not None and away_goals is not None:
                self._process_match_statistics(match_details, jornada_id, home_team_id, away_team_id)
            return match_id
        return None
    
    def _process_match_statistics(self, match_details: Dict, jornada_id: str, home_team_id: str, away_team_id: str):
        """Process REAL match statistics from API data"""
        match_data = match_details.get('match', match_details)
        
        # Extract data
        goals = match_data.get('goals', [])
        bookings = match_data.get('bookings', [])
        substitutions = match_data.get('substitutions', [])
        home_lineup = match_data.get('homeTeam', {}).get('lineup', [])
        away_lineup = match_data.get('awayTeam', {}).get('lineup', [])
        
        # Process both teams
        self._process_team_statistics(home_lineup, home_team_id, jornada_id, goals, bookings, substitutions, True)
        self._process_team_statistics(away_lineup, away_team_id, jornada_id, goals, bookings, substitutions, False)
    
    def _process_team_statistics(self, lineup: List[Dict], team_id: str, jornada_id: str, 
                                  goals: List[Dict], bookings: List[Dict], substitutions: List[Dict], is_home: bool):
        """Process statistics for one team"""
        if not lineup:
            return
        
        # Get team name for filtering
        cursor = self.conn.cursor()
        
        for player in lineup:
            player_id = str(player.get('id'))
            
            # Check if player exists in our database
            if not self.fetch_one("SELECT 1 FROM FantasyChamp.Jogador WHERE ID = ?", (player_id,)):
                continue
            
            stats = {
                'TempoJogo': 90,  # Default to full match
                'GolosSofridos': 0,
                'GolosMarcados': 0,
                'Assistencias': 0,
                'CartoesAmarelos': 0,
                'CartoesVermelhos': 0
            }
            
            # Count goals scored by this player
            for goal in goals:
                scorer = goal.get('scorer', {})
                if scorer and str(scorer.get('id')) == player_id:
                    stats['GolosMarcados'] += 1
                
                # Count assists
                assist = goal.get('assist')
                if assist and str(assist.get('id')) == player_id:
                    stats['Assistencias'] += 1
            
            # Count cards
            for booking in bookings:
                booking_player = booking.get('player', {})
                if booking_player and str(booking_player.get('id')) == player_id:
                    card_type = booking.get('card', '')
                    if card_type == 'YELLOW_CARD':
                        stats['CartoesAmarelos'] += 1
                    elif card_type == 'RED_CARD':
                        stats['CartoesVermelhos'] += 1
                        # Reduce playing time on red card
                        minute = booking.get('minute', 90)
                        stats['TempoJogo'] = min(stats['TempoJogo'], minute)
            
            # Check substitutions
            for sub in substitutions:
                player_out = sub.get('playerOut', {})
                player_in = sub.get('playerIn', {})
                minute = sub.get('minute', 0)
                
                if player_out and str(player_out.get('id')) == player_id:
                    # Player was substituted out
                    stats['TempoJogo'] = min(stats['TempoJogo'], minute)
                elif player_in and str(player_in.get('id')) == player_id:
                    # Player came on as substitute
                    stats['TempoJogo'] = 90 - minute
            
            # Goals conceded (for GK/Defenders who played most of the match)
            position = player.get('position', '')
            if position in ['Goalkeeper', 'Defender'] and stats['TempoJogo'] >= 60:
                # Get opponent's goals from the match
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
            
            # Insert player statistics
            self.insert_player_pontuacao(player_id, jornada_id, stats)
    
    def populate_player_statistics_for_matchdays(self):
        """Generate REALISTIC statistics for matchdays 1-4 ONLY"""
        print(f"\n📊 Generating realistic player statistics for matchdays 1-4...")
        
        total_stats = 0
        
        for matchday in range(1, 5):  # 🔥 ONLY 1-4
            jornada_id = f"J{matchday:03d}"
            
            if not self.fetch_one("SELECT 1 FROM FantasyChamp.Jornada WHERE ID = ?", (jornada_id,)):
                print(f"  ⚠️  Jornada {matchday} not found, skipping...")
                continue
            
            print(f"\n  Matchday {matchday}:")
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ID, ID_Clube1, ID_Clube2, golos_clube1, golos_clube2
                FROM FantasyChamp.Jogo
                WHERE ID_jornada = ?
            """, jornada_id)
            
            matches = cursor.fetchall()
            matches_processed = 0
            
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
                matches_processed += 1
            
            print(f"    ✓ Generated stats for {matches_processed} matches")
        
        print(f"\n✓ Total player statistics generated: {total_stats}")
        return total_stats
    
    def _create_match_stats_for_team(self, players: list, goals_scored: int, goals_conceded: int, jornada_id: str):
        """Create realistic stats ensuring goals = assists"""
        if not players:
            return
        
        num_players = min(14, len(players))
        playing = random.sample(players, num_players)
        
        if not playing:
            return
        
        # Distribute goals among attackers
        goal_scorers = []
        if goals_scored > 0:
            attackers = [(p, pos) for p, pos in playing if pos in ['Forward', 'Midfielder']]
            if attackers:
                goal_scorers = random.choices(attackers, k=goals_scored)
            else:
                goal_scorers = random.choices(playing, k=goals_scored)
        
        # 🔥 CRITICAL: Each goal has EXACTLY 1 assist
        assists = []
        for _ in range(goals_scored):
            potential_assisters = [(p, pos) for p, pos in playing if pos in ['Midfielder', 'Forward']]
            if potential_assisters:
                assists.append(random.choice(potential_assisters))
            elif playing:
                assists.append(random.choice(playing))
        
        # Create stats for all playing players
        for player_id, position in playing:
            stats = {
                'TempoJogo': 0,
                'GolosSofridos': 0,
                'GolosMarcados': 0,
                'Assistencias': 0,
                'CartoesAmarelos': 0,
                'CartoesVermelhos': 0
            }
            
            # Playing time
            starter_idx = playing.index((player_id, position))
            if starter_idx < 11:
                stats['TempoJogo'] = random.choice([90, 90, 90, 85, 80])
            else:
                stats['TempoJogo'] = random.choice([15, 20, 25, 30])
            
            # Goals
            stats['GolosMarcados'] = sum(1 for (p, _) in goal_scorers if p == player_id)
            
            # Assists
            stats['Assistencias'] = sum(1 for (p, _) in assists if p == player_id)
            
            # Goals conceded (GK/Defenders)
            if position in ['Goalkeeper', 'Defender'] and stats['TempoJogo'] >= 45:
                stats['GolosSofridos'] = goals_conceded
            
            # Cards
            if random.random() < 0.15:
                stats['CartoesAmarelos'] = 1
            if random.random() < 0.02:
                stats['CartoesVermelhos'] = 1
                stats['TempoJogo'] = min(stats['TempoJogo'], random.randint(30, 70))
            
            self.insert_player_pontuacao(player_id, jornada_id, stats)
    
    def insert_player_pontuacao(self, player_id: str, jornada_id: str, stats: Dict) -> bool:
        query = """
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Jogador 
                          WHERE ID_jogador = ? AND ID_jornada = ?)
            INSERT INTO FantasyChamp.Pontuação_Jogador 
                (ID_jogador, ID_jornada, TempoJogo, GolosSofridos, GolosMarcados, 
                 Assistencias, CartoesAmarelos, CartoesVermelhos, pontuação_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        pontuacao = 0
        if stats['TempoJogo'] >= 30:
            pontuacao += stats['TempoJogo'] // 30
        
        pontuacao += stats['GolosMarcados'] * 5
        pontuacao += stats['Assistencias'] * 3
        pontuacao -= stats['CartoesAmarelos'] * 1
        pontuacao -= stats['CartoesVermelhos'] * 3
        
        pontuacao_str = str(pontuacao)
        
        return self.execute_query(
            query,
            (player_id, jornada_id, 
             player_id, jornada_id,
             stats['TempoJogo'], stats['GolosSofridos'], stats['GolosMarcados'],
             stats['Assistencias'], stats['CartoesAmarelos'], stats['CartoesVermelhos'],
             pontuacao_str)
        )


def main():
    print("=" * 70)
    print("UEFA Champions League Data Population")
    print("MATCHDAYS 1-4 ONLY")
    print("=" * 70)
    
    if not API_KEY:
        print("\n❌ ERROR: FOOTBALL_DATA_KEY not found in .env")
        return
    
    api = FootballDataClient(API_KEY)
    db = DatabaseManager(DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD)
    
    if not db.connect():
        return
    
    try:
        clean = input("\n⚠️  Clean existing data? (y/n): ").lower()
        if clean == 'y':
            db.clean_game_data()
        
        print(f"\n🔥 Fetching Champions League teams...")
        teams = api.get_teams(CHAMPIONS_LEAGUE_ID, SEASON)
        print(f"✓ Found {len(teams)} teams\n")
        
        print("💾 Inserting teams...")
        for team in teams:
            db.insert_team(team)
        
        print(f"\n👥 Fetching players...")
        total_players = 0
        
        for i, team in enumerate(teams, 1):
            team_id = team['id']
            team_name = team['name']
            
            print(f"\n[{i}/{len(teams)}] {team_name}:")
            
            team_details = api.get_team_details(team_id)
            
            if team_details and 'squad' in team_details:
                squad = team_details['squad']
                for player in squad:
                    if db.insert_player(player, str(team_id)):
                        total_players += 1
                
                print(f"  ✓ Inserted {len(squad)} players")
        
        print(f"\n✓ Total players: {total_players}")
        
        print(f"\n⚽ Fetching matches (ONLY matchdays 1-4)...")
        matches = api.get_matches(CHAMPIONS_LEAGUE_ID, SEASON)
        
        # 🔥 Filter to ONLY matchdays 1-4
        matches_1_to_4 = [m for m in matches if 1 <= (m.get('matchday') or 0) <= 4]
        print(f"✓ Found {len(matches_1_to_4)} matches in matchdays 1-4")
        
        print("\n💾 Inserting matches with REAL player statistics...")
        matches_inserted = 0
        stats_processed = 0
        
        for i, match in enumerate(matches_1_to_4, 1):
            match_id_api = match.get('id')
            
            # Check if match has finished (has scores)
            score = match.get('score', {}).get('fullTime', {})
            if score.get('home') is None or score.get('away') is None:
                print(f"  [{i}/{len(matches_1_to_4)}] Skipping unfinished match")
                continue
            
            print(f"  [{i}/{len(matches_1_to_4)}] {match['homeTeam']['name']} vs {match['awayTeam']['name']}", end="")
            
            # Get detailed match data (lineup, goals, assists, cards)
            match_details = api.get_match_details(match_id_api)
            
            if match_details:
                match_db_id = db.insert_match(match, match_details)
                if match_db_id:
                    matches_inserted += 1
                    stats_processed += 1
                    print(f" ✓ (with real stats)")
                else:
                    print(f" ✗")
            else:
                # Insert match without detailed stats
                match_db_id = db.insert_match(match)
                if match_db_id:
                    matches_inserted += 1
                    print(f" ✓ (no details available)")
                else:
                    print(f" ✗")
        
        print(f"\n✓ Inserted {matches_inserted} matches")
        print(f"✓ Processed {stats_processed} matches with real player statistics")
        
        print(f"\n" + "=" * 70)
        print("✅ COMPLETE!")
        print("=" * 70)
        print(f"Teams: {len(teams)}")
        print(f"Players: {total_players}")
        print(f"Matches: {matches_inserted} (Matchdays 1-4 ONLY)")
        print(f"Matches with REAL player stats: {stats_processed}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()