"""
Script para criar 5 utilizadores demo com equipas completas
"""
import sys
from pathlib import Path
import random

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection
from persistence.users import create_user
from persistence.equipa import criar_equipa, adicionar_jogador_equipa
from persistence.players import list_all

utilizadores = [
    {'first': 'Joao', 'last': 'Silva', 'email': 'joao.silva@demo.com', 'password': 'demo123', 'country': 'POR', 'nationality': 'POR', 'birthdate': '1995-03-15', 'team_name': 'FC Silva'},
    {'first': 'Maria', 'last': 'Santos', 'email': 'maria.santos@demo.com', 'password': 'demo123', 'country': 'POR', 'nationality': 'POR', 'birthdate': '1998-07-22', 'team_name': 'Santos United'},
    {'first': 'Pedro', 'last': 'Costa', 'email': 'pedro.costa@demo.com', 'password': 'demo123', 'country': 'POR', 'nationality': 'POR', 'birthdate': '1992-11-08', 'team_name': 'Costa FC'},
    {'first': 'Ana', 'last': 'Oliveira', 'email': 'ana.oliveira@demo.com', 'password': 'demo123', 'country': 'POR', 'nationality': 'POR', 'birthdate': '1996-05-30', 'team_name': 'Oliveira Stars'},
    {'first': 'Rui', 'last': 'Ferreira', 'email': 'rui.ferreira@demo.com', 'password': 'demo123', 'country': 'POR', 'nationality': 'POR', 'birthdate': '1994-09-17', 'team_name': 'Ferreira Team'}
]

print("=" * 70)
print(" CRIANDO 5 UTILIZADORES DEMO ".center(70))
print("=" * 70)

# Obter jogadores
todos_jogadores = list_all()
grs = [j for j in todos_jogadores if j.posicao == 'Goalkeeper']
defesas = [j for j in todos_jogadores if j.posicao == 'Defender']
medios = [j for j in todos_jogadores if j.posicao == 'Midfielder']
avancados = [j for j in todos_jogadores if j.posicao == 'Forward']

print(f"\nJogadores: GR={len(grs)}, DEF={len(defesas)}, MED={len(medios)}, AV={len(avancados)}\n")

criados = 0

for i, user_data in enumerate(utilizadores, 1):
    print(f"[{i}/5] {user_data['first']} {user_data['last']}...")
    
    try:
        # Criar utilizador
        user_id = create_user(user_data['first'], user_data['last'], user_data['email'], user_data['password'], user_data['country'], user_data['nationality'], user_data['birthdate'])
        
        if not user_id:
            print(f"  [ERRO] Falha ao criar utilizador\n")
            continue
        
        # Criar equipa
        equipa_id = criar_equipa(user_data['team_name'], user_id)
        
        # Adicionar 15 jogadores (2 GR, 5 DEF, 5 MED, 3 AV)
        for gr in random.sample(grs, 2):
            adicionar_jogador_equipa(equipa_id, gr.id)
            grs.remove(gr)
        
        for defesa in random.sample(defesas, 5):
            adicionar_jogador_equipa(equipa_id, defesa.id)
            defesas.remove(defesa)
        
        for medio in random.sample(medios, 5):
            adicionar_jogador_equipa(equipa_id, medio.id)
            medios.remove(medio)
        
        for avancado in random.sample(avancados, 3):
            adicionar_jogador_equipa(equipa_id, avancado.id)
            avancados.remove(avancado)
        
        # Calcular pontuacoes para jornadas 1-4
        with create_connection() as conn:
            cursor = conn.cursor()
            pontuacao_acumulada = 0
            
            for jornada_num in range(1, 5):
                jornada_id = f"J{jornada_num:03d}"
                try:
                    # Usar SP que insere na tabela Pontuacao_Equipa
                    cursor.execute("""
                        DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                        EXEC FantasyChamp.AtualizarPontuacaoEquipa
                            @ID_Equipa = ?, @ID_Jornada = ?,
                            @Resultado = @Resultado OUTPUT,
                            @Mensagem = @Mensagem OUTPUT;
                    """, equipa_id, jornada_id)
                    
                    # Obter pontuacao e atualizar acumulada
                    cursor.execute("""
                        SELECT pontuação_jornada 
                        FROM FantasyChamp.Pontuação_Equipa
                        WHERE ID_Equipa = ? AND ID_jornada = ?
                    """, equipa_id, jornada_id)
                    
                    pont_row = cursor.fetchone()
                    if pont_row:
                        pontuacao_acumulada += pont_row[0]
                        cursor.execute("""
                            UPDATE FantasyChamp.Pontuação_Equipa
                            SET pontuação_acumulada = ?
                            WHERE ID_Equipa = ? AND ID_jornada = ?
                        """, pontuacao_acumulada, equipa_id, jornada_id)
                    
                    conn.commit()
                except:
                    pass
        
        print(f"  [OK] {user_data['first']} criado com equipa '{user_data['team_name']}'\n")
        criados += 1
        
    except Exception as e:
        print(f"  [ERRO] {e}\n")

print("=" * 70)
print(f" CONCLUIDO: {criados}/5 utilizadores criados ".center(70))
print("=" * 70)
print("\nCredenciais: Email=[nome].[apelido]@demo.com | Password=demo123")
print("=" * 70)
