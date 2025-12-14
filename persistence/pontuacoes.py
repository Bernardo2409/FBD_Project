from persistence.session import create_connection

# Função para calcular a pontuação de um jogador
def calcular_pontuacao_jogador(id_jogador: str, id_jornada: str) -> int:
    """
    Função que calcula a pontuação total de um jogador para uma jornada específica
    e atualiza o valor de `pontuação_total` na tabela Pontuação_Jogador.
    """
    with create_connection() as conn:
        cursor = conn.cursor()

        # Obter as estatísticas do jogador da tabela Pontuação_Jogador
        cursor.execute("""
            SELECT GolosMarcados, Assistencias, CartoesAmarelos, CartoesVermelhos, TempoJogo 
            FROM FantasyChamp.Pontuação_Jogador 
            WHERE ID_jogador = ? AND ID_jornada = ?
        """, id_jogador, id_jornada)

        row = cursor.fetchone()
        
        if not row:
            return 0  # Se não encontrar o jogador para a jornada, retorna 0
        
        # Calculando a pontuação total do jogador
        pontos = 0
        pontos += row.GolosMarcados * 5  # 5 pontos por gol
        pontos += row.Assistencias * 3  # 3 pontos por assistência
        pontos -= row.CartoesAmarelos * 1  # -1 ponto por cartão amarelo
        pontos -= row.CartoesVermelhos * 3  # -3 pontos por cartão vermelho
        pontos += (row.TempoJogo // 30)  # 1 ponto para cada 30 minutos de jogo

        # Atualizar a pontuação total na tabela Pontuação_Jogador
        cursor.execute("""
            UPDATE FantasyChamp.Pontuação_Jogador
            SET pontuação_total = ?
            WHERE ID_jogador = ? AND ID_jornada = ?
        """, pontos, id_jogador, id_jornada)

        conn.commit()
        return pontos

# Função para calcular a pontuação de uma equipa (soma as pontuações dos jogadores)
def calcular_pontuacao_equipa(id_equipa: str, id_jornada: str) -> int:
    """
    Função que calcula a pontuação total de uma equipa para uma jornada específica
    somando a pontuação de todos os jogadores da equipa.
    """
    with create_connection() as conn:
        cursor = conn.cursor()

        # Obter todos os jogadores da equipa na jornada
        cursor.execute("""
            SELECT P.ID_Jogador
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Pontuação_Jogador P ON PE.ID_Jogador = P.ID_Jogador
            WHERE PE.ID_Equipa = ? AND P.ID_jornada = ?
        """, id_equipa, id_jornada)

        jogadores = cursor.fetchall()

        pontuacao_total = 0
        for jogador in jogadores:
            jogador_id = jogador.ID_Jogador
            # Calcular a pontuação de cada jogador
            pontuacao_jogador = calcular_pontuacao_jogador(jogador_id, id_jornada)
            pontuacao_total += pontuacao_jogador


        conn.commit()
        return pontuacao_total

# Função para atualizar a pontuação de todos os jogadores e equipas
def atualizar_pontuacoes():
    """
    Função para calcular e atualizar a pontuação de todas as equipas e jogadores para a jornada 1.
    """
    with create_connection() as conn:
        cursor = conn.cursor()

        # Obter todas as equipas
        cursor.execute("SELECT ID FROM FantasyChamp.Equipa")
        equipas = cursor.fetchall()

        for equipa in equipas:
            equipa_id = equipa.ID
            # Atualizar a pontuação da equipa para a jornada 1
            id_jornada = 'jornada_1'  # Alterar conforme a lógica de jornadas (fixar para jornada 1)
            calcular_pontuacao_equipa(equipa_id, id_jornada)

        conn.commit()

# Função para calcular a pontuação de um jogador específico para todas as suas jornadas
def calcular_pontuacao_jogador_especifico(id_jogador: str):
    """
    Função que calcula a pontuação total de um jogador para todas as suas jornadas.
    """
    with create_connection() as conn:
        cursor = conn.cursor()

        # Obter todas as jornadas em que o jogador participou
        cursor.execute("""
            SELECT DISTINCT ID_jornada 
            FROM FantasyChamp.Pontuação_Jogador
            WHERE ID_jogador = ?
        """, id_jogador)

        jornadas = cursor.fetchall()

        # Para cada jornada, calcular a pontuação do jogador
        for jornada in jornadas:
            id_jornada = jornada.ID_jornada
            calcular_pontuacao_jogador(id_jogador, id_jornada)

        conn.commit()

# Função para obter as pontuações por jornada de uma equipa
def obter_pontuacoes_jornadas(id_equipa: str):
    """
    Função que retorna a pontuação de uma equipa para cada jornada com totais acumulados.
    """
    with create_connection() as conn:
        cursor = conn.cursor()

        # Obter todas as jornadas com pontuação da equipa
        cursor.execute("""
            SELECT 
                PJ.ID_jornada as jornada,
                SUM(CAST(PJ.pontuação_total AS INT)) as pontuacao
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Pontuação_Jogador PJ ON PE.ID_Jogador = PJ.ID_Jogador
            WHERE PE.ID_Equipa = ?
            GROUP BY PJ.ID_jornada
            ORDER BY PJ.ID_jornada
        """, id_equipa)

        jornadas_data = cursor.fetchall()
        
        # Calcular pontuação acumulada
        pontuacoes = []
        acumulada = 0
        
        for jornada in jornadas_data:
            acumulada += jornada.pontuacao or 0
            pontuacoes.append({
                'jornada': jornada.jornada,
                'pontuacao': jornada.pontuacao or 0,
                'pontuacao_acumulada': acumulada
            })
        
        return pontuacoes

