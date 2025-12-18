"""
Script to calculate team points using batch stored procedure
"""
from persistence.session import create_connection

def main():
    print("=" * 70)
    print("Calculating Team Points for All Teams (Batch)")
    print("=" * 70)
    
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        print("\nExecuting sp_AtualizarPontuacoesBatch...")
        print("This will calculate points for all teams across all matchdays.\n")
        
        # Execute batch update stored procedure
        cursor.execute("""
            DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
            
            EXEC FantasyChamp.sp_AtualizarPontuacoesBatch
                @Resultado = @Resultado OUTPUT,
                @Mensagem = @Mensagem OUTPUT;
            
            SELECT @Resultado AS Resultado, @Mensagem AS Mensagem;
        """)
        
        result = cursor.fetchone()
        
        if result:
            sucesso = result.Resultado
            mensagem = result.Mensagem
            
            if sucesso:
                print(f"SUCCESS: {mensagem}")
                conn.commit()
            else:
                print(f"ERROR: {mensagem}")
                conn.rollback()
        else:
            print("ERROR: No result returned from stored procedure")
            conn.rollback()
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("Done!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
