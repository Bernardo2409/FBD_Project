from persistence.session import create_connection
import pyodbc

# Função para calcular a pontuação de um jogador usando stored procedure
def calcular_pontuacao_jogador(id_jogador: str, id_jornada: str) -> int:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DECLARE @Pontuacao INT, @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC CalcularPontuacaoJogador 
                    @ID_Jogador = ?,
                    @ID_Jornada = ?,
                    @Pontuacao = @Pontuacao OUTPUT,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Pontuacao, @Resultado, @Mensagem;
            """, id_jogador, id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                pontuacao = row[0]
                resultado = row[1]
                mensagem = row[2]
                
                if resultado == 0:
                    raise Exception(f"Erro ao calcular pontuação: {mensagem}")
                
                conn.commit()
                return pontuacao
            else:
                conn.rollback()
                raise Exception("Nenhum resultado retornado da stored procedure")
                
        except pyodbc.Error as e:
            conn.rollback()
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise e

# Função para calcular a pontuação de uma equipa usando stored procedure
def calcular_pontuacao_equipa(id_equipa: str, id_jornada: str) -> int:
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DECLARE @PontuacaoTotal INT, @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC CalcularPontuacaoEquipa 
                    @ID_Equipa = ?,
                    @ID_Jornada = ?,
                    @PontuacaoTotal = @PontuacaoTotal OUTPUT,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @PontuacaoTotal, @Resultado, @Mensagem;
            """, id_equipa, id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                pontuacao_total = row[0]
                resultado = row[1]
                mensagem = row[2]
                
                if resultado == 0:
                    raise Exception(f"Erro ao calcular pontuação da equipa: {mensagem}")
                
                conn.commit()
                return pontuacao_total
            else:
                conn.rollback()
                raise Exception("Nenhum resultado retornado da stored procedure")
                
        except pyodbc.Error as e:
            conn.rollback()
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise e

# Função para atualizar pontuação na tabela Pontuação_Equipa usando stored procedure
def atualizar_pontuacao_equipa_tabela(id_equipa: str, id_jornada: str):
    """
    Atualiza a pontuação de uma equipa na tabela Pontuação_Equipa
    usando a stored procedure sp_AtualizarPontuacaoEquipa.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_AtualizarPontuacaoEquipa 
                    @ID_Equipa = ?,
                    @ID_Jornada = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Resultado, @Mensagem;
            """, id_equipa, id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                resultado = row[0]
                mensagem = row[1]
                
                if resultado == 0:
                    raise Exception(f"Erro ao atualizar pontuação: {mensagem}")
                
                conn.commit()
                return mensagem
            else:
                conn.rollback()
                raise Exception("Nenhum resultado retornado da stored procedure")
                
        except pyodbc.Error as e:
            conn.rollback()
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise e

# Função para atualizar a pontuação de todos os jogadores e equipas
def atualizar_pontuacoes():
    """
    Calcula e atualiza a pontuação de todas as equipas e jogadores para todas as jornadas.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Obter todas as jornadas
            cursor.execute("SELECT ID FROM FantasyChamp.Jornada ORDER BY Numero")
            jornadas = cursor.fetchall()
            
            if not jornadas:
                print("Nenhuma jornada encontrada")
                return
            
            # Obter todas as equipas
            cursor.execute("SELECT ID FROM FantasyChamp.Equipa")
            equipas = cursor.fetchall()
            
            if not equipas:
                print("Nenhuma equipa encontrada")
                return
            
            print(f"Atualizando pontuações para {len(equipas)} equipas em {len(jornadas)} jornadas...")
            
            for i, equipa in enumerate(equipas, 1):
                equipa_id = equipa.ID
                print(f"Processando equipa {i}/{len(equipas)}: {equipa_id}")
                
                for jornada in jornadas:
                    id_jornada = jornada.ID
                    try:
                        # Atualizar pontuação da equipa para esta jornada
                        mensagem = atualizar_pontuacao_equipa_tabela(equipa_id, id_jornada)
                        print(f"  Jornada {id_jornada}: {mensagem}")
                        
                    except Exception as e:
                        print(f"  Erro na jornada {id_jornada}: {str(e)}")
                        continue
            
            print("Atualização de pontuações concluída!")
            
        except pyodbc.Error as e:
            print(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            print(f"Erro: {str(e)}")

# Função para calcular a pontuação de um jogador específico para todas as suas jornadas
def calcular_pontuacao_jogador_especifico(id_jogador: str):
    """
    Calcula a pontuação total de um jogador para todas as suas jornadas.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Obter todas as jornadas em que o jogador participou
            cursor.execute("""
                SELECT DISTINCT ID_jornada 
                FROM FantasyChamp.Pontuação_Jogador
                WHERE ID_jogador = ?
            """, id_jogador)

            jornadas = cursor.fetchall()
            
            if not jornadas:
                print(f"Jogador {id_jogador} não tem registos em nenhuma jornada")
                return

            print(f"Calculando pontuação para jogador {id_jogador} em {len(jornadas)} jornadas...")
            
            total_pontuacao = 0
            # Para cada jornada, calcular a pontuação do jogador
            for jornada in jornadas:
                id_jornada = jornada.ID_jornada
                try:
                    pontuacao = calcular_pontuacao_jogador(id_jogador, id_jornada)
                    total_pontuacao += pontuacao
                    print(f"  Jornada {id_jornada}: {pontuacao} pontos")
                except Exception as e:
                    print(f"  Erro na jornada {id_jornada}: {str(e)}")
                    continue
            
            print(f"Pontuação total do jogador {id_jogador}: {total_pontuacao} pontos")
            
        except pyodbc.Error as e:
            print(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            print(f"Erro: {str(e)}")

# Função para obter as pontuações por jornada de uma equipa usando stored procedure
def obter_pontuacoes_jornadas(id_equipa: str):
    """
    Retorna a pontuação de uma equipa para cada jornada.
    Usa a stored procedure sp_ObterPontuacoesJornadasEquipa.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Primeiro, criar a stored procedure se não existir
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_ObterPontuacoesJornadasEquipa')
                BEGIN
                    EXEC('
                    CREATE PROCEDURE sp_ObterPontuacoesJornadasEquipa
                        @ID_Equipa UNIQUEIDENTIFIER,
                        @Resultado BIT OUTPUT,
                        @Mensagem NVARCHAR(200) OUTPUT
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        
                        BEGIN TRY
                            -- Ler da tabela Pontuação_Equipa
                            SELECT 
                                J.ID AS JornadaID,
                                J.Numero AS JornadaNumero,
                                ISNULL(PE.pontuação_jornada, 0) AS PontuacaoJornada,
                                ISNULL(PE.pontuação_acumulada, 0) AS PontuacaoAcumulada,
                                J.Data_Inicio,
                                J.Data_Fim
                            FROM FantasyChamp.Jornada J
                            LEFT JOIN FantasyChamp.Pontuação_Equipa PE 
                                ON J.ID = PE.ID_jornada AND PE.ID_Equipa = @ID_Equipa
                            ORDER BY J.Numero;
                            
                            SET @Resultado = 1;
                            SET @Mensagem = ''Dados obtidos com sucesso'';
                        END TRY
                        BEGIN CATCH
                            SET @Resultado = 0;
                            SET @Mensagem = ''Erro: '' + ERROR_MESSAGE();
                        END CATCH
                    END')
                END
            """)
            
            # Agora usar a stored procedure
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_ObterPontuacoesJornadasEquipa 
                    @ID_Equipa = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
            """, id_equipa)
            
            # Obter os resultados
            pontuacoes = []
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    pontuacao = dict(zip(columns, row))
                    pontuacoes.append({
                        'jornada_id': pontuacao.get('JornadaID'),
                        'jornada_numero': pontuacao.get('JornadaNumero'),
                        'pontuacao': pontuacao.get('PontuacaoJornada'),
                        'pontuacao_acumulada': pontuacao.get('PontuacaoAcumulada'),
                        'data_inicio': pontuacao.get('Data_Inicio'),
                        'data_fim': pontuacao.get('Data_Fim')
                    })
            
            return pontuacoes
            
        except pyodbc.Error as e:
            print(f"Erro de banco de dados: {str(e)}")
            return []
        except Exception as e:
            print(f"Erro: {str(e)}")
            return []

# Função para calcular e atualizar pontuações de forma otimizada
def atualizar_pontuacoes_otimizado():
    """
    Atualiza pontuações de forma otimizada usando stored procedures em batch.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Criar stored procedure para atualização em batch se não existir
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_AtualizarPontuacoesBatch')
                BEGIN
                    EXEC('
                    CREATE PROCEDURE sp_AtualizarPontuacoesBatch
                        @Resultado BIT OUTPUT,
                        @Mensagem NVARCHAR(200) OUTPUT
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        
                        DECLARE @ID_Equipa UNIQUEIDENTIFIER;
                        DECLARE @ID_Jornada VARCHAR(16);
                        DECLARE @CountEquipas INT = 0;
                        DECLARE @CountJornadas INT = 0;
                        DECLARE @CountTotal INT = 0;
                        
                        BEGIN TRY
                            -- Criar cursor para todas as equipas e jornadas
                            DECLARE cursor_equipas_jornadas CURSOR FOR
                                SELECT E.ID, J.ID
                                FROM FantasyChamp.Equipa E
                                CROSS JOIN FantasyChamp.Jornada J
                                ORDER BY E.ID, J.ID;
                            
                            OPEN cursor_equipas_jornadas;
                            FETCH NEXT FROM cursor_equipas_jornadas INTO @ID_Equipa, @ID_Jornada;
                            
                            WHILE @@FETCH_STATUS = 0
                            BEGIN
                                -- Atualizar pontuação para esta equipa e jornada
                                EXEC sp_AtualizarPontuacaoEquipa 
                                    @ID_Equipa = @ID_Equipa,
                                    @ID_Jornada = @ID_Jornada,
                                    @Resultado = @Resultado OUTPUT,
                                    @Mensagem = @Mensagem OUTPUT;
                                
                                SET @CountTotal = @CountTotal + 1;
                                IF @CountTotal % 100 = 0
                                    PRINT ''Processados '' + CAST(@CountTotal AS NVARCHAR(10)) + '' registos...'';
                                
                                FETCH NEXT FROM cursor_equipas_jornadas INTO @ID_Equipa, @ID_Jornada;
                            END
                            
                            CLOSE cursor_equipas_jornadas;
                            DEALLOCATE cursor_equipas_jornadas;
                            
                            SET @Resultado = 1;
                            SET @Mensagem = ''Atualização concluída. '' + CAST(@CountTotal AS NVARCHAR(10)) + '' registos processados.'';
                            
                        END TRY
                        BEGIN CATCH
                            SET @Resultado = 0;
                            SET @Mensagem = ''Erro: '' + ERROR_MESSAGE();
                            
                            IF CURSOR_STATUS(''global'', ''cursor_equipas_jornadas'') >= 0
                            BEGIN
                                CLOSE cursor_equipas_jornadas;
                                DEALLOCATE cursor_equipas_jornadas;
                            END
                        END CATCH
                    END')
                END
            """)
            
            # Executar a stored procedure de batch
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_AtualizarPontuacoesBatch 
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
                
                SELECT @Resultado, @Mensagem;
            """)
            
            row = cursor.fetchone()
            
            if row:
                resultado = row[0]
                mensagem = row[1]
                
                if resultado == 0:
                    print(f"Erro: {mensagem}")
                else:
                    print(f"Sucesso: {mensagem}")
            
            conn.commit()
            
        except pyodbc.Error as e:
            conn.rollback()
            print(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            conn.rollback()
            print(f"Erro: {str(e)}")

# Adicionar estas funções ao arquivo pontuacoes.py

def obter_equipa_com_pontuacoes_jornada(id_equipa: str, id_jornada: str):
    """
    Obtém todos os dados da equipa para uma jornada específica.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Primeiro, verificar se existe uma stored procedure específica
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_ObterEquipaJornadaCompleta')
                BEGIN
                    EXEC('
                    CREATE PROCEDURE sp_ObterEquipaJornadaCompleta
                        @ID_Equipa UNIQUEIDENTIFIER,
                        @ID_Jornada VARCHAR(16),
                        @Resultado BIT OUTPUT,
                        @Mensagem NVARCHAR(200) OUTPUT
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        
                        DECLARE @PontuacaoTotal INT = 0;
                        DECLARE @CountJogadores INT = 0;
                        
                        BEGIN TRY
                            -- Obter lista de jogadores com pontuações
                            SELECT 
                                J.ID AS JogadorID,
                                J.Nome AS Nome,
                                P.Posição AS Posicao,
                                C.Nome AS Clube,
                                C.clube_imagem AS ImagemClube,
                                J.jogador_imagem AS ImagemJogador,
                                PE.benched AS NoBanco,
                                ISNULL(PJ.GolosMarcados, 0) AS GolosMarcados,
                                ISNULL(PJ.Assistencias, 0) AS Assistencias,
                                ISNULL(PJ.CartoesAmarelos, 0) AS CartoesAmarelos,
                                ISNULL(PJ.CartoesVermelhos, 0) AS CartoesVermelhos,
                                ISNULL(PJ.TempoJogo, 0) AS TempoJogo,
                                dbo.fn_CalcularPontuacaoJogador(J.ID, @ID_Jornada) AS Pontuacao
                            FROM FantasyChamp.Pertence PE
                            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
                            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
                            JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
                            LEFT JOIN FantasyChamp.Pontuação_Jogador PJ 
                                ON J.ID = PJ.ID_Jogador AND PJ.ID_jornada = @ID_Jornada
                            WHERE PE.ID_Equipa = @ID_Equipa
                            ORDER BY 
                                CASE WHEN P.Posição = ''Goalkeeper'' THEN 1
                                     WHEN P.Posição = ''Defender'' THEN 2
                                     WHEN P.Posição = ''Midfielder'' THEN 3
                                     WHEN P.Posição = ''Forward'' THEN 4
                                     ELSE 5 END,
                                CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
                                J.Nome;
                            
                            -- Calcular pontuação total
                            SELECT @PontuacaoTotal = SUM(dbo.fn_CalcularPontuacaoJogador(PE.ID_Jogador, @ID_Jornada))
                            FROM FantasyChamp.Pertence PE
                            WHERE PE.ID_Equipa = @ID_Equipa AND PE.benched = 0;
                            
                            -- Retornar pontuação total separadamente
                            SELECT @PontuacaoTotal AS PontuacaoTotal;
                            
                            SET @Resultado = 1;
                            SET @Mensagem = ''Dados obtidos com sucesso'';
                            
                        END TRY
                        BEGIN CATCH
                            SET @Resultado = 0;
                            SET @Mensagem = ''Erro: '' + ERROR_MESSAGE();
                        END CATCH
                    END')
                END
            """)
            
            # Executar a stored procedure
            cursor.execute("""
                DECLARE @Resultado BIT, @Mensagem NVARCHAR(200);
                
                EXEC sp_ObterEquipaJornadaCompleta 
                    @ID_Equipa = ?,
                    @ID_Jornada = ?,
                    @Resultado = @Resultado OUTPUT,
                    @Mensagem = @Mensagem OUTPUT;
            """, id_equipa, id_jornada)
            
            # Obter resultados
            jogadores = []
            pontuacao_total = 0
            
            # Primeiro conjunto: lista de jogadores
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    jogador = dict(zip(columns, row))
                    jogador['pontuacao'] = jogador.get('Pontuacao', 0)
                    jogador['benched'] = jogador.get('NoBanco', 1)
                    jogador['posicao'] = jogador.get('Posicao', '')
                    jogadores.append(jogador)
            
            # Segundo conjunto: pontuação total
            if cursor.nextset() and cursor.description:
                columns = [column[0] for column in cursor.description]
                row = cursor.fetchone()
                if row:
                    pontuacao_total = row[0]
            
            return {
                'jogadores': jogadores,
                'pontuacao_total': pontuacao_total
            }
            
        except pyodbc.Error as e:
            raise Exception(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            raise e

def obter_jornada_info(id_jornada: str):
    """
    Obtém informações de uma jornada específica.
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ID, Numero, Data_Inicio, Data_Fim
                FROM FantasyChamp.Jornada
                WHERE ID = ?
            """, id_jornada)
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'numero': row[1],
                    'data_inicio': row[2],
                    'data_fim': row[3]
                }
            else:
                return None
                
        except pyodbc.Error as e:
            print(f"Erro ao obter jornada info: {e}")
            return None