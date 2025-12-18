"""
Script para gerar estatísticas fictícias (mas coerentes) para jogadores
dos jogos reais que já existem na base de dados.

- Jogadores: REAIS
- Clubes: REAIS  
- Jogos e resultados: REAIS
- Estatísticas individuais: FICTÍCIAS mas coerentes com os resultados
"""

import sys
from pathlib import Path
import random

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection


def limpar_estatisticas_jogadores():
    """Limpa todas as estatísticas de jogadores"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM FantasyChamp.Pontuação_Jogador")
        conn.commit()
        print("✅ Estatísticas de jogadores limpas!\n")


def obter_jogos():
    """Obtém todos os jogos com resultados"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                J.ID,
                J.ID_Clube1,
                J.ID_Clube2,
                J.ID_jornada,
                J.golos_clube1,
                J.golos_clube2,
                C1.Nome AS Clube1,
                C2.Nome AS Clube2
            FROM FantasyChamp.Jogo J
            JOIN FantasyChamp.Clube C1 ON J.ID_Clube1 = C1.ID
            JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID
            WHERE J.golos_clube1 IS NOT NULL 
              AND J.golos_clube2 IS NOT NULL
            ORDER BY J.ID_jornada, J.ID
        """)
        
        jogos = []
        for row in cursor:
            jogos.append({
                'jogo_id': row.ID,
                'clube1_id': row.ID_Clube1,
                'clube2_id': row.ID_Clube2,
                'jornada_id': row.ID_jornada,
                'golos_clube1': row.golos_clube1,
                'golos_clube2': row.golos_clube2,
                'clube1_nome': row.Clube1,
                'clube2_nome': row.Clube2
            })
        
        return jogos


def obter_jogadores_clube(clube_id):
    """Obtém todos os jogadores de um clube com suas posições"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                J.ID,
                J.Nome,
                P.Posição
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE J.ID_clube = ?
            ORDER BY 
                CASE P.Posição
                    WHEN 'Goalkeeper' THEN 1
                    WHEN 'Defender' THEN 2
                    WHEN 'Midfielder' THEN 3
                    WHEN 'Forward' THEN 4
                END
        """)
        
        jogadores = []
        for row in cursor:
            jogadores.append({
                'id': row.ID,
                'nome': row.Nome,
                'posicao': row.Posição
            })
        
        return jogadores


def gerar_estatisticas_equipa(jogadores, golos_marcados, golos_sofridos, jornada_id):
    """
    Gera estatísticas fictícias mas coerentes para uma equipa
    
    Args:
        jogadores: Lista de jogadores do clube
        golos_marcados: Golos que a equipa marcou
        golos_sofridos: Golos que a equipa sofreu
        jornada_id: ID da jornada
    
    Returns:
        Lista de estatísticas por jogador
    """
    if not jogadores:
        return []
    
    # Selecionar 11 titulares e 3-5 suplentes
    num_titulares = min(11, len(jogadores))
    num_suplentes = min(random.randint(3, 5), max(0, len(jogadores) - num_titulares))
    
    titulares = jogadores[:num_titulares]
    suplentes = jogadores[num_titulares:num_titulares + num_suplentes] if num_suplentes > 0 else []
    
    stats_list = []
    
    # Distribuir golos entre atacantes e médios
    atacantes = [j for j in titulares if j['posicao'] in ['Forward', 'Midfielder']]
    if not atacantes and golos_marcados > 0:
        atacantes = titulares  # Se não houver atacantes, qualquer um pode marcar
    
    # Lista de quem marca cada golo
    marcadores = []
    assistentes = []
    
    if golos_marcados > 0 and atacantes:
        marcadores = random.choices(atacantes, k=golos_marcados)
        # Cada golo pode ou não ter assistência (70% de probabilidade)
        for _ in range(golos_marcados):
            if random.random() < 0.7:
                assistente = random.choice([j for j in titulares if j['posicao'] in ['Midfielder', 'Forward']])
                assistentes.append(assistente)
    
    # Gerar stats para titulares
    for jogador in titulares:
        stats = {
            'id_jogador': jogador['id'],
            'id_jornada': jornada_id,
            'tempo_jogo': random.choice([90, 90, 90, 85, 80, 75]),  # Maioria joga 90
            'golos_marcados': sum(1 for m in marcadores if m['id'] == jogador['id']),
            'assistencias': sum(1 for a in assistentes if a['id'] == jogador['id']),
            'golos_sofridos': 0,
            'cartoes_amarelos': 1 if random.random() < 0.15 else 0,
            'cartoes_vermelhos': 1 if random.random() < 0.02 else 0
        }
        
        # Golos sofridos para GR e defesas que jogaram mais de 60 min
        if jogador['posicao'] in ['Goalkeeper', 'Defender'] and stats['tempo_jogo'] >= 60:
            stats['golos_sofridos'] = golos_sofridos
        
        # Se levou vermelho, reduzir tempo de jogo
        if stats['cartoes_vermelhos'] > 0:
            stats['tempo_jogo'] = random.randint(30, 70)
        
        stats_list.append(stats)
    
    # Gerar stats para suplentes (menos tempo de jogo)
    for jogador in suplentes:
        stats = {
            'id_jogador': jogador['id'],
            'id_jornada': jornada_id,
            'tempo_jogo': random.choice([10, 15, 20, 25, 30]),
            'golos_marcados': 0,
            'assistencias': 0,
            'golos_sofridos': 0,
            'cartoes_amarelos': 1 if random.random() < 0.05 else 0,
            'cartoes_vermelhos': 0
        }
        
        stats_list.append(stats)
    
    return stats_list


def calcular_pontuacao(stats):
    """Calcula a pontuação total de um jogador baseado nas estatísticas"""
    pontuacao = 0
    
    # Pontos por tempo de jogo
    if stats['tempo_jogo'] >= 60:
        pontuacao += 2
    elif stats['tempo_jogo'] >= 30:
        pontuacao += 1
    
    # Pontos por golos
    pontuacao += stats['golos_marcados'] * 5
    
    # Pontos por assistências
    pontuacao += stats['assistencias'] * 3
    
    # Penalização por golos sofridos (GR/Defesas)
    if stats['golos_sofridos'] > 0:
        pontuacao -= min(stats['golos_sofridos'], 2)  # Máximo -2 pontos
    
    # Penalização por cartões
    pontuacao -= stats['cartoes_amarelos'] * 1
    pontuacao -= stats['cartoes_vermelhos'] * 3
    
    return max(0, pontuacao)  # Não pode ser negativo


def inserir_estatisticas(stats_list):
    """Insere estatísticas na base de dados"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        for stats in stats_list:
            pontuacao_total = calcular_pontuacao(stats)
            
            cursor.execute("""
                INSERT INTO FantasyChamp.Pontuação_Jogador
                (ID_jogador, ID_jornada, TempoJogo, GolosSofridos, GolosMarcados,
                 Assistencias, CartoesAmarelos, CartoesVermelhos, pontuação_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
                stats['id_jogador'],
                stats['id_jornada'],
                stats['tempo_jogo'],
                stats['golos_sofridos'],
                stats['golos_marcados'],
                stats['assistencias'],
                stats['cartoes_amarelos'],
                stats['cartoes_vermelhos'],
                str(pontuacao_total)
            )
        
        conn.commit()


def gerar_todas_estatisticas():
    """Gera estatísticas para todos os jogos"""
    print("="*70)
    print(" GERAÇÃO DE ESTATÍSTICAS FICTÍCIAS ".center(70))
    print("="*70)
    print()
    
    # Obter todos os jogos
    jogos = obter_jogos()
    
    if not jogos:
        print("❌ Nenhum jogo encontrado na base de dados!")
        print("   Execute primeiro o populate_db.py para adicionar jogos.")
        return
    
    print(f"📊 Encontrados {len(jogos)} jogos\n")
    
    # Confirmar
    resposta = input("⚠️  Isto vai LIMPAR e GERAR novas estatísticas. Continuar? (s/n): ")
    if resposta.lower() != 's':
        print("❌ Operação cancelada!")
        return
    
    # Limpar estatísticas existentes
    limpar_estatisticas_jogadores()
    
    print("🎲 A gerar estatísticas fictícias...\n")
    
    total_stats = 0
    
    for i, jogo in enumerate(jogos, 1):
        print(f"[{i}/{len(jogos)}] {jogo['clube1_nome']} {jogo['golos_clube1']}-{jogo['golos_clube2']} {jogo['clube2_nome']}")
        
        # Obter jogadores de cada clube
        jogadores_clube1 = obter_jogadores_clube(jogo['clube1_id'])
        jogadores_clube2 = obter_jogadores_clube(jogo['clube2_id'])
        
        if not jogadores_clube1:
            print(f"  ⚠️  Nenhum jogador encontrado para {jogo['clube1_nome']}")
        if not jogadores_clube2:
            print(f"  ⚠️  Nenhum jogador encontrado para {jogo['clube2_nome']}")
        
        # Gerar estatísticas para clube 1
        if jogadores_clube1:
            stats_clube1 = gerar_estatisticas_equipa(
                jogadores_clube1,
                jogo['golos_clube1'],
                jogo['golos_clube2'],
                jogo['jornada_id']
            )
            inserir_estatisticas(stats_clube1)
            total_stats += len(stats_clube1)
            print(f"  ✓ {len(stats_clube1)} jogadores de {jogo['clube1_nome']}")
        
        # Gerar estatísticas para clube 2
        if jogadores_clube2:
            stats_clube2 = gerar_estatisticas_equipa(
                jogadores_clube2,
                jogo['golos_clube2'],
                jogo['golos_clube1'],
                jogo['jornada_id']
            )
            inserir_estatisticas(stats_clube2)
            total_stats += len(stats_clube2)
            print(f"  ✓ {len(stats_clube2)} jogadores de {jogo['clube2_nome']}")
    
    print("\n" + "="*70)
    print(" ✅ ESTATÍSTICAS GERADAS COM SUCESSO! ".center(70))
    print("="*70)
    print(f"Total de estatísticas criadas: {total_stats}")
    print(f"Jogos processados: {len(jogos)}")
    print("="*70)


def verificar_estatisticas():
    """Mostra resumo das estatísticas geradas"""
    print("\n" + "="*70)
    print(" VERIFICAÇÃO DE ESTATÍSTICAS ".center(70))
    print("="*70)
    print()
    
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Total de estatísticas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM FantasyChamp.Pontuação_Jogador
        """)
        total = cursor.fetchone().total
        
        # Top marcadores
        cursor.execute("""
            SELECT TOP 10
                J.Nome,
                C.Nome as Clube,
                SUM(PJ.GolosMarcados) as Golos,
                SUM(PJ.Assistencias) as Assistencias
            FROM FantasyChamp.Pontuação_Jogador PJ
            JOIN FantasyChamp.Jogador J ON PJ.ID_jogador = J.ID
            JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
            GROUP BY J.Nome, C.Nome
            HAVING SUM(PJ.GolosMarcados) > 0
            ORDER BY Golos DESC, Assistencias DESC
        """)
        
        print(f"📊 Total de estatísticas: {total}\n")
        print("⚽ TOP 10 MARCADORES:")
        print("-"*70)
        print(f"{'Jogador':<30} {'Clube':<25} {'Golos':>7} {'Assist':>7}")
        print("-"*70)
        
        for row in cursor:
            print(f"{row.Nome[:29]:<30} {row.Clube[:24]:<25} {row.Golos:>7} {row.Assistencias:>7}")
        
        print("="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verificar_estatisticas()
    else:
        gerar_todas_estatisticas()
        print("\n💡 Para ver estatísticas, execute: python generate_player_stats.py --verify")
