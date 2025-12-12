import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection


# ============================================================================
# PARTE 1: CRIAR ESTRUTURA DA BASE DE DADOS
# ============================================================================

def criar_tabela_pontuacao_equipa():
    """
    Cria a tabela Pontuação_Equipa se não existir
    
    Estrutura:
    - ID_Equipa: referência à equipa do utilizador
    - ID_jornada: qual jornada
    - pontuação_jornada: pontos ganhos nesta jornada
    - pontuação_acumulada: soma de todas as jornadas até agora
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'FantasyChamp' 
            AND TABLE_NAME = 'Pontuação_Equipa'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("[INFO] Tabela Pontuação_Equipa já existe")
            resposta = input("Queres recriar a tabela? (s/n): ")
            if resposta.lower() == 's':
                cursor.execute("DROP TABLE FantasyChamp.Pontuação_Equipa")
                print("[INFO] Tabela antiga removida")
            else:
                return
        
        # Criar tabela
        cursor.execute("""
            CREATE TABLE FantasyChamp.Pontuação_Equipa (
                ID_Equipa UNIQUEIDENTIFIER NOT NULL,
                ID_jornada VARCHAR(10) NOT NULL,
                pontuação_jornada INT DEFAULT 0,
                pontuação_acumulada INT DEFAULT 0,
                data_calculo DATETIME DEFAULT GETDATE(),
                
                PRIMARY KEY (ID_Equipa, ID_jornada),
                FOREIGN KEY (ID_Equipa) REFERENCES FantasyChamp.Equipa(ID)
            )
        """)
        
        conn.commit()
        print("✅ Tabela Pontuação_Equipa criada com sucesso!\n")


# ============================================================================
# PARTE 2: CALCULAR PONTUAÇÕES
# ============================================================================

def obter_jogadores_equipa_em_campo(id_equipa):
    """
    Obtém os jogadores que estão EM CAMPO (benched = 0)
    Estes são os que contam para a pontuação!
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, P.Posição
            FROM FantasyChamp.Jogador J
            JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = ? AND PE.benched = 0
        """, id_equipa)
        
        jogadores = []
        for row in cursor:
            jogadores.append({
                'id': row.ID,
                'nome': row.Nome,
                'posicao': row.Posição
            })
        
        return jogadores


def calcular_pontuacao_equipa_jornada(id_equipa, id_jornada):
    """
    Calcula a pontuação da equipa para uma jornada específica
    
    Retorna:
    - pontos_jornada: pontos ganhos nesta jornada
    - detalhes: lista com pontuação de cada jogador
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter jogadores em campo
        jogadores_campo = obter_jogadores_equipa_em_campo(id_equipa)
        
        if not jogadores_campo:
            return 0, []
        
        pontos_total = 0
        detalhes = []
        
        for jogador in jogadores_campo:
            # Buscar pontuação do jogador nesta jornada
            cursor.execute("""
                SELECT pontuação_total, GolosMarcados, Assistencias, 
                       CartoesAmarelos, CartoesVermelhos, TempoJogo
                FROM FantasyChamp.Pontuação_Jogador
                WHERE ID_jogador = ? AND ID_jornada = ?
            """, jogador['id'], id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                pontos_jogador = row.pontuação_total
                pontos_total += pontos_jogador
                
                detalhes.append({
                    'jogador': jogador['nome'],
                    'posicao': jogador['posicao'],
                    'pontos': pontos_jogador,
                    'golos': row.GolosMarcados,
                    'assistencias': row.Assistencias,
                    'amarelos': row.CartoesAmarelos,
                    'vermelhos': row.CartoesVermelhos,
                    'minutos': row.TempoJogo
                })
            else:
                # Jogador não jogou esta jornada
                detalhes.append({
                    'jogador': jogador['nome'],
                    'posicao': jogador['posicao'],
                    'pontos': 0,
                    'golos': 0,
                    'assistencias': 0,
                    'amarelos': 0,
                    'vermelhos': 0,
                    'minutos': 0
                })
        
        return pontos_total, detalhes


def guardar_pontuacao_equipa(id_equipa, id_jornada, pontos_jornada):
    """
    Guarda a pontuação da equipa na base de dados
    E atualiza o total acumulado
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Calcular pontuação acumulada até esta jornada
        cursor.execute("""
            SELECT ISNULL(SUM(pontuação_jornada), 0)
            FROM FantasyChamp.Pontuação_Equipa
            WHERE ID_Equipa = ? AND ID_jornada < ?
        """, id_equipa, id_jornada)
        
        pontos_anteriores = cursor.fetchone()[0]
        pontos_acumulados = pontos_anteriores + pontos_jornada
        
        # Verificar se já existe registo para esta jornada
        cursor.execute("""
            SELECT 1 FROM FantasyChamp.Pontuação_Equipa
            WHERE ID_Equipa = ? AND ID_jornada = ?
        """, id_equipa, id_jornada)
        
        if cursor.fetchone():
            # Atualizar
            cursor.execute("""
                UPDATE FantasyChamp.Pontuação_Equipa
                SET pontuação_jornada = ?,
                    pontuação_acumulada = ?,
                    data_calculo = GETDATE()
                WHERE ID_Equipa = ? AND ID_jornada = ?
            """, pontos_jornada, pontos_acumulados, id_equipa, id_jornada)
        else:
            # Inserir
            cursor.execute("""
                INSERT INTO FantasyChamp.Pontuação_Equipa
                (ID_Equipa, ID_jornada, pontuação_jornada, pontuação_acumulada)
                VALUES (?, ?, ?, ?)
            """, id_equipa, id_jornada, pontos_jornada, pontos_acumulados)
        
        conn.commit()
        
        return pontos_acumulados


def atualizar_pontuacao_total_equipa(id_equipa):
    """
    Atualiza o campo PontuaçãoTotal na tabela Equipa
    com a soma de todas as jornadas
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ISNULL(SUM(pontuação_jornada), 0)
            FROM FantasyChamp.Pontuação_Equipa
            WHERE ID_Equipa = ?
        """, id_equipa)
        
        total = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE FantasyChamp.Equipa
            SET PontuaçãoTotal = ?
            WHERE ID = ?
        """, total, id_equipa)
        
        conn.commit()
        
        return total


# ============================================================================
# PARTE 3: PROCESSAR TODAS AS EQUIPAS
# ============================================================================

def processar_equipa(id_equipa, nome_equipa, jornadas):
    """Processa uma equipa para todas as jornadas"""
    print(f"\n{'='*70}")
    print(f" {nome_equipa} ".center(70))
    print('='*70)
    
    for jornada in jornadas:
        pontos, detalhes = calcular_pontuacao_equipa_jornada(id_equipa, jornada)
        
        if pontos > 0:
            pontos_acum = guardar_pontuacao_equipa(id_equipa, jornada, pontos)
            print(f"\n📊 {jornada}: {pontos} pontos (Total: {pontos_acum})")
            
            # Mostrar top 3 jogadores
            detalhes_ordenados = sorted(detalhes, key=lambda x: x['pontos'], reverse=True)
            for i, d in enumerate(detalhes_ordenados[:3], 1):
                print(f"  {i}. {d['jogador']} ({d['posicao']}): {d['pontos']} pts")
        else:
            print(f"\n📊 {jornada}: 0 pontos (sem jogadores ou não jogaram)")
    
    # Atualizar total
    total = atualizar_pontuacao_total_equipa(id_equipa)
    print(f"\n✅ Total Final: {total} pontos")


def processar_todas_equipas():
    """Processa todas as equipas do sistema"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter todas as equipas
        cursor.execute("""
            SELECT E.ID, E.Nome, U.PrimeiroNome, U.Apelido
            FROM FantasyChamp.Equipa E
            JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
        """)
        
        equipas = cursor.fetchall()
        
        if not equipas:
            print("❌ Nenhuma equipa encontrada!")
            return
        
        # Obter todas as jornadas disponíveis
        cursor.execute("""
            SELECT DISTINCT ID_jornada
            FROM FantasyChamp.Jogo
            ORDER BY ID_jornada
        """)
        
        jornadas = [row.ID_jornada for row in cursor.fetchall()]
        
        if not jornadas:
            print("❌ Nenhuma jornada encontrada! Cria jogos primeiro.")
            return
        
        print(f"\n{'='*70}")
        print(f" PROCESSANDO {len(equipas)} EQUIPAS ".center(70))
        print(f" {len(jornadas)} jornadas disponíveis ".center(70))
        print('='*70)
        
        for equipa in equipas:
            nome_completo = f"{equipa.Nome} ({equipa.PrimeiroNome} {equipa.Apelido})"
            processar_equipa(equipa.ID, nome_completo, jornadas)
        
        print(f"\n{'='*70}")
        print(" ✅ TODAS AS EQUIPAS PROCESSADAS! ".center(70))
        print('='*70)


def mostrar_classificacao():
    """Mostra a classificação geral de todas as equipas"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                E.Nome AS Equipa,
                U.PrimeiroNome + ' ' + U.Apelido AS Utilizador,
                E.PontuaçãoTotal,
                E.Orçamento
            FROM FantasyChamp.Equipa E
            JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
            ORDER BY E.PontuaçãoTotal DESC
        """)
        
        equipas = cursor.fetchall()
        
        if not equipas:
            print("❌ Nenhuma equipa encontrada!")
            return
        
        print(f"\n{'='*70}")
        print(" 🏆 CLASSIFICAÇÃO GERAL ".center(70))
        print('='*70)
        print(f"{'POS':<5} {'EQUIPA':<25} {'UTILIZADOR':<20} {'PONTOS':>10}")
        print('-'*70)
        
        for i, eq in enumerate(equipas, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{emoji}{i:<3} {eq.Equipa[:24]:<25} {eq.Utilizador[:19]:<20} {eq.PontuaçãoTotal:>10}")
        
        print('='*70 + "\n")


def ver_detalhes_equipa(id_equipa=None):
    """Mostra detalhes da pontuação de uma equipa específica"""
    with create_connection() as conn:
        cursor = conn.cursor()
        
        if not id_equipa:
            # Listar equipas para escolher
            cursor.execute("""
                SELECT E.ID, E.Nome, U.PrimeiroNome + ' ' + U.Apelido AS Utilizador
                FROM FantasyChamp.Equipa E
                JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
                ORDER BY E.Nome
            """)
            
            equipas = cursor.fetchall()
            
            print("\n📋 Equipas disponíveis:")
            for i, eq in enumerate(equipas, 1):
                print(f"{i}. {eq.Nome} ({eq.Utilizador})")
            
            escolha = input("\nEscolhe uma equipa (número): ").strip()
            if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(equipas):
                print("❌ Escolha inválida!")
                return
            
            id_equipa = equipas[int(escolha) - 1].ID
        
        # Obter info da equipa
        cursor.execute("""
            SELECT E.Nome, U.PrimeiroNome + ' ' + U.Apelido AS Utilizador,
                   E.PontuaçãoTotal, E.Orçamento
            FROM FantasyChamp.Equipa E
            JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
            WHERE E.ID = ?
        """, id_equipa)
        
        equipa = cursor.fetchone()
        
        print(f"\n{'='*70}")
        print(f" {equipa.Nome} ".center(70))
        print(f" Gestor: {equipa.Utilizador} ".center(70))
        print('='*70)
        print(f"💰 Orçamento restante: {equipa.Orçamento:.2f}M")
        print(f"⭐ Pontuação total: {equipa.PontuaçãoTotal} pontos\n")
        
        # Obter pontuações por jornada
        cursor.execute("""
            SELECT ID_jornada, pontuação_jornada, pontuação_acumulada
            FROM FantasyChamp.Pontuação_Equipa
            WHERE ID_Equipa = ?
            ORDER BY ID_jornada
        """, id_equipa)
        
        print(f"{'JORNADA':<15} {'PONTOS':<15} {'ACUMULADO':<15}")
        print('-'*45)
        
        for row in cursor:
            print(f"{row.ID_jornada:<15} {row.pontuação_jornada:<15} {row.pontuação_acumulada:<15}")
        
        print('='*70 + "\n")


# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def menu():
    """Menu interativo"""
    print("=" * 70)
    print(" SISTEMA DE PONTUAÇÃO DE EQUIPAS FANTASY ".center(70))
    print("=" * 70)
    print()
    print("1. Criar/Recriar tabela Pontuação_Equipa")
    print("2. Calcular pontuações de TODAS as equipas")
    print("3. Calcular pontuação de UMA equipa específica")
    print("4. Ver classificação geral")
    print("5. Ver detalhes de uma equipa")
    print("0. Sair")
    print()
    
    escolha = input("Escolhe uma opção: ").strip()
    return escolha


if __name__ == "__main__":
    while True:
        escolha = menu()
        
        if escolha == '1':
            print("\n" + "="*70)
            print(" CRIAR TABELA ".center(70))
            print("="*70 + "\n")
            criar_tabela_pontuacao_equipa()
            input("\nPressiona ENTER para continuar...")
        
        elif escolha == '2':
            print("\n" + "="*70)
            print(" CALCULAR TODAS AS EQUIPAS ".center(70))
            print("="*70)
            processar_todas_equipas()
            input("\nPressiona ENTER para continuar...")
        
        elif escolha == '3':
            print("\n" + "="*70)
            print(" CALCULAR UMA EQUIPA ".center(70))
            print("="*70)
            
            with create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT E.ID, E.Nome, U.PrimeiroNome + ' ' + U.Apelido AS Utilizador
                    FROM FantasyChamp.Equipa E
                    JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
                    ORDER BY E.Nome
                """)
                equipas = cursor.fetchall()
            
            print("\n📋 Equipas disponíveis:")
            for i, eq in enumerate(equipas, 1):
                print(f"{i}. {eq.Nome} ({eq.Utilizador})")
            
            escolha_eq = input("\nEscolhe uma equipa (número): ").strip()
            if escolha_eq.isdigit() and 1 <= int(escolha_eq) <= len(equipas):
                eq = equipas[int(escolha_eq) - 1]
                
                with create_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT ID_jornada
                        FROM FantasyChamp.Jogo
                        ORDER BY ID_jornada
                    """)
                    jornadas = [row.ID_jornada for row in cursor.fetchall()]
                
                processar_equipa(eq.ID, eq.Nome, jornadas)
            else:
                print("❌ Escolha inválida!")
            
            input("\nPressiona ENTER para continuar...")
        
        elif escolha == '4':
            mostrar_classificacao()
            input("\nPressiona ENTER para continuar...")
        
        elif escolha == '5':
            ver_detalhes_equipa()
            input("\nPressiona ENTER para continuar...")
        
        elif escolha == '0':
            print("\n👋 Até já!")
            break
        
        else:
            print("\n❌ Opção inválida!\n")
            input("Pressiona ENTER para continuar...")