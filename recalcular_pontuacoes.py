"""
Recalcula todas as pontuações dos jogadores usando o SP atualizado
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from persistence.session import create_connection

def recalcular_pontuacoes():
    print("="*70)
    print(" RECALCULANDO PONTUAÇÕES ".center(70))
    print("="*70)
    print()
    
    with create_connection() as conn:
        cursor = conn.cursor()
        
        # Obter todos os registos de pontuação
        cursor.execute("""
            SELECT ID_jogador, ID_jornada
            FROM FantasyChamp.Pontuação_Jogador
        """)
        
        registos = cursor.fetchall()
        total = len(registos)
        
        print(f"📊 Encontrados {total} registos para recalcular\n")
        
        sucessos = 0
        erros = 0
        
        for i, (jogador_id, jornada_id) in enumerate(registos, 1):
            try:
                cursor.execute("""
                    DECLARE @Pontuacao INT, @Resultado BIT, @Mensagem NVARCHAR(200);
                    EXEC FantasyChamp.CalcularPontuacaoJogador
                        @ID_Jogador = ?,
                        @ID_Jornada = ?,
                        @Pontuacao = @Pontuacao OUTPUT,
                        @Resultado = @Resultado OUTPUT,
                        @Mensagem = @Mensagem OUTPUT;
                        
                    UPDATE FantasyChamp.Pontuação_Jogador
                    SET pontuação_total = CAST(@Pontuacao AS VARCHAR(10))
                    WHERE ID_jogador = ? AND ID_jornada = ?;
                """, jogador_id, jornada_id, jogador_id, jornada_id)
                
                sucessos += 1
                
                if i % 50 == 0:
                    print(f"  Processados {i}/{total}...")
                    
            except Exception as e:
                erros += 1
                print(f"  ⚠️  Erro no jogador {jogador_id}, jornada {jornada_id}: {e}")
        
        conn.commit()
        
        print(f"\n✅ Recálculo completo!")
        print(f"   Sucessos: {sucessos}")
        print(f"   Erros: {erros}")
        print("="*70)

if __name__ == "__main__":
    recalcular_pontuacoes()
