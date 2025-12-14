import sys
from pathlib import Path
import random

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection


def limpar_tabela_pontuacao_equipa():
    """Limpa todos os dados da tabela Pontuação_Equipa"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM FantasyChamp.Pontuação_Equipa")
        conn.commit()
        print("✅ Tabela Pontuação_Equipa limpa!\n")


def obter_equipas():
    """Obtém todas as equipas do sistema"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT E.ID, E.Nome, U.PrimeiroNome + ' ' + U.Apelido AS Utilizador
            FROM FantasyChamp.Equipa E
            JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
            WHERE U.PrimeiroNome != 'Sistema'
        """)
        
        equipas = []
        for row in cursor:
            equipas.append({
                'id': row.ID,
                'nome': row.Nome,
                'utilizador': row.Utilizador
            })
        
        return equipas


def obter_jornadas():
    """Obtém todas as jornadas disponíveis"""
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ID_jornada
            FROM FantasyChamp.Jogo
            ORDER BY ID_jornada
        """)
        
        jornadas = [row.ID_jornada for row in cursor.fetchall()]
        
        # Se não houver jornadas na tabela Jogo, criar algumas fictícias
        if not jornadas:
            jornadas = [f'jornada_{i}' for i in range(1, 6)]
        
        return jornadas


def gerar_pontuacoes_aleatorias(id_equipa, jornadas):
    """
    Gera pontuações aleatórias para uma equipa em todas as jornadas
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        pontuacao_acumulada = 0
        
        for jornada in jornadas:
            # Gerar pontuação aleatória entre 30 e 120 pontos
            pontuacao_jornada = random.randint(30, 120)
            pontuacao_acumulada += pontuacao_jornada
            
            # Inserir na base de dados
            cursor.execute("""
                INSERT INTO FantasyChamp.Pontuação_Equipa 
                (ID_Equipa, ID_jornada, pontuação_jornada, pontuação_acumulada)
                VALUES (?, ?, ?, ?)
            """, id_equipa, jornada, pontuacao_jornada, pontuacao_acumulada)
        
        # Atualizar PontuaçãoTotal na tabela Equipa
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET PontuaçãoTotal = ?
            WHERE ID = ?
        """, pontuacao_acumulada, id_equipa)
        
        conn.commit()
        
        return pontuacao_acumulada


def popular_pontuacoes_teste():
    """
    Popula a tabela Pontuação_Equipa com dados de teste
    """
    print("="*70)
    print(" SCRIPT DE TESTE - PONTUAÇÕES DAS EQUIPAS ".center(70))
    print("="*70)
    print()
    
    # Obter equipas
    equipas = obter_equipas()
    
    if not equipas:
        print("❌ Nenhuma equipa encontrada no sistema!")
        return
    
    print(f"📊 Encontradas {len(equipas)} equipas\n")
    
    # Obter jornadas
    jornadas = obter_jornadas()
    print(f"🏆 Jornadas disponíveis: {', '.join(jornadas)}\n")
    
    # Confirmar ação
    resposta = input("⚠️  Isto vai LIMPAR todas as pontuações existentes. Continuar? (s/n): ")
    if resposta.lower() != 's':
        print("❌ Operação cancelada!")
        return
    
    # Limpar tabela
    limpar_tabela_pontuacao_equipa()
    
    # Gerar pontuações para cada equipa
    print("🎲 A gerar pontuações aleatórias...\n")
    
    for equipa in equipas:
        total = gerar_pontuacoes_aleatorias(equipa['id'], jornadas)
        print(f"✅ {equipa['nome']} ({equipa['utilizador']}): {total} pontos totais")
    
    print("\n" + "="*70)
    print(" ✅ DADOS DE TESTE GERADOS COM SUCESSO! ".center(70))
    print("="*70)


def verificar_pontuacoes():
    """
    Verifica e mostra as pontuações geradas
    """
    print("\n" + "="*70)
    print(" VERIFICAÇÃO DE PONTUAÇÕES ".center(70))
    print("="*70)
    print()
    
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Ranking geral
        cursor.execute("""
            SELECT 
                E.Nome AS Equipa,
                U.PrimeiroNome + ' ' + U.Apelido AS Utilizador,
                E.PontuaçãoTotal,
                COUNT(PE.ID_jornada) AS NumJornadas
            FROM FantasyChamp.Equipa E
            JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
            LEFT JOIN FantasyChamp.Pontuação_Equipa PE ON E.ID = PE.ID_Equipa
            WHERE U.PrimeiroNome != 'Sistema'
            GROUP BY E.Nome, U.PrimeiroNome, U.Apelido, E.PontuaçãoTotal
            ORDER BY E.PontuaçãoTotal DESC
        """)
        
        print("🏆 RANKING GERAL:")
        print("-"*70)
        print(f"{'Pos':<5} {'Equipa':<25} {'Utilizador':<20} {'Pontos':>10} {'Jornadas':>10}")
        print("-"*70)
        
        for i, row in enumerate(cursor, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            pontos = row.PontuaçãoTotal if row.PontuaçãoTotal else 0
            print(f"{emoji}{i:<3} {row.Equipa[:24]:<25} {row.Utilizador[:19]:<20} {pontos:>10} {row.NumJornadas:>10}")
        
        print("="*70)


def mostrar_detalhes_equipa():
    """
    Mostra detalhes de pontuação por jornada de uma equipa específica
    """
    equipas = obter_equipas()
    
    if not equipas:
        print("❌ Nenhuma equipa encontrada!")
        return
    
    print("\n📋 Equipas disponíveis:")
    for i, eq in enumerate(equipas, 1):
        print(f"{i}. {eq['nome']} ({eq['utilizador']})")
    
    escolha = input("\nEscolhe uma equipa (número): ").strip()
    
    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(equipas):
        print("❌ Escolha inválida!")
        return
    
    equipa = equipas[int(escolha) - 1]
    
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ID_jornada,
                pontuação_jornada,
                pontuação_acumulada,
                data_calculo
            FROM FantasyChamp.Pontuação_Equipa
            WHERE ID_Equipa = ?
            ORDER BY ID_jornada
        """, equipa['id'])
        
        print(f"\n{'='*70}")
        print(f" {equipa['nome']} - {equipa['utilizador']} ".center(70))
        print('='*70)
        print(f"{'Jornada':<15} {'Pontos':<15} {'Acumulado':<15} {'Data':<25}")
        print('-'*70)
        
        for row in cursor:
            data_str = row.data_calculo.strftime('%Y-%m-%d %H:%M:%S') if row.data_calculo else 'N/A'
            print(f"{row.ID_jornada:<15} {row.pontuação_jornada:<15} {row.pontuação_acumulada:<15} {data_str:<25}")
        
        print('='*70)


def menu_principal():
    """Menu interativo"""
    while True:
        print("\n" + "="*70)
        print(" SCRIPT DE TESTE - PONTUAÇÕES ".center(70))
        print("="*70)
        print()
        print("1. Gerar dados de teste (limpa e cria novos)")
        print("2. Verificar ranking geral")
        print("3. Ver detalhes de uma equipa")
        print("4. Limpar todas as pontuações")
        print("0. Sair")
        print()
        
        escolha = input("Escolhe uma opção: ").strip()
        
        if escolha == '1':
            popular_pontuacoes_teste()
        elif escolha == '2':
            verificar_pontuacoes()
        elif escolha == '3':
            mostrar_detalhes_equipa()
        elif escolha == '4':
            resposta = input("⚠️  Tens a certeza? (s/n): ")
            if resposta.lower() == 's':
                limpar_tabela_pontuacao_equipa()
        elif escolha == '0':
            print("\n👋 Até já!")
            break
        else:
            print("\n❌ Opção inválida!")
        
        input("\nPressiona ENTER para continuar...")


if __name__ == "__main__":
    menu_principal()