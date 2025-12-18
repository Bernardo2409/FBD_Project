"""
Script para calcular e inserir pontuacoes das equipas demo
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection

print("="*70)
print(" CALCULANDO E INSERINDO PONTUACOES DAS EQUIPAS ".center(70))
print("="*70)
print()

conn = create_connection()
cursor = conn.cursor()

# Obter equipas dos utilizadores demo
cursor.execute("""
    SELECT E.ID, E.Nome, U.PrimeiroNome, U.Apelido
    FROM FantasyChamp.Equipa E
    JOIN FantasyChamp.Utilizador U ON E.ID_Utilizador = U.ID
    WHERE U.Email LIKE '%@demo.com'
    ORDER BY U.PrimeiroNome
""")

equipas = cursor.fetchall()

print(f"Encontradas {len(equipas)} equipas\n")

total_calculado = 0

for equipa_id, equipa_nome, primeiro_nome, apelido in equipas:
    print(f"{primeiro_nome} {apelido} - {equipa_nome}")
    
    pontuacao_acumulada = 0
    
    for jornada_num in range(1, 5):
        jornada_id = f"J{jornada_num:03d}"
        
        try:
            # Usar SP que INSERE na tabela
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC FantasyChamp.AtualizarPontuacaoEquipa
                    @ID_Equipa = ?,
                    @ID_Jornada = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Resultado, @Mensagem;
            """, equipa_id, jornada_id)
            
            result = cursor.fetchone()
            sucesso = result[0]
            mensagem = result[1]
            
            if sucesso:
                # Obter a pontuacao que foi inserida
                cursor.execute("""
                    SELECT pontuação_jornada 
                    FROM FantasyChamp.Pontuação_Equipa
                    WHERE ID_Equipa = ? AND ID_jornada = ?
                """, equipa_id, jornada_id)
                
                pont_row = cursor.fetchone()
                pontuacao_jornada = pont_row[0] if pont_row else 0
                pontuacao_acumulada += pontuacao_jornada
                
                # Atualizar com pontuacao acumulada
                cursor.execute("""
                    UPDATE FantasyChamp.Pontuação_Equipa
                    SET pontuação_acumulada = ?
                    WHERE ID_Equipa = ? AND ID_jornada = ?
                """, pontuacao_acumulada, equipa_id, jornada_id)
                
                print(f"  J{jornada_num}: {pontuacao_jornada} pts (Acum: {pontuacao_acumulada})")
                total_calculado += 1
            else:
                print(f"  J{jornada_num}: ERRO - {mensagem}")
            
            conn.commit()
            
        except Exception as e:
            print(f"  J{jornada_num}: ERRO - {e}")
            conn.rollback()
    
    print()

conn.close()

print("="*70)
print(f" CONCLUIDO: {total_calculado} pontuacoes inseridas ".center(70))
print("="*70)
