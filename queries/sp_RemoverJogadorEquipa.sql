ALTER PROCEDURE FantasyChamp.RemoverJogadorEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jogador varchar(16)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Preco_Jogador DECIMAL(10,2);
    DECLARE @EstavaNoCampo BIT;
    DECLARE @Posicao NVARCHAR(50);
    DECLARE @JogadorBancoPromover VARCHAR(16);

    BEGIN TRANSACTION;

    -- Obter preço, posição e status do jogador
    SELECT @Preco_Jogador = J.Preço,
           @Posicao = POS.Posição,
           @EstavaNoCampo = CASE WHEN P.benched = 0 THEN 1 ELSE 0 END
    FROM FantasyChamp.Jogador J
    INNER JOIN FantasyChamp.Pertence P ON J.ID = P.ID_Jogador
    INNER JOIN FantasyChamp.Posição POS ON J.ID_Posição = POS.ID
    WHERE P.ID_Equipa = @ID_Equipa
      AND P.ID_Jogador = @ID_Jogador;

    -- Se encontrou jogador na equipa
    IF @Preco_Jogador IS NOT NULL
    BEGIN
        -- Remover da equipa
        DELETE FROM FantasyChamp.Pertence
        WHERE ID_Equipa = @ID_Equipa
          AND ID_Jogador = @ID_Jogador;

        -- Devolver dinheiro
        UPDATE FantasyChamp.Equipa
        SET Orçamento = Orçamento + @Preco_Jogador
        WHERE ID = @ID_Equipa;

        -- Se o jogador removido estava no campo, promover um do banco da mesma posição
        IF @EstavaNoCampo = 1
        BEGIN
            -- Encontrar um jogador do banco da mesma posição
            SELECT TOP 1 @JogadorBancoPromover = PE.ID_Jogador
            FROM FantasyChamp.Pertence PE
            INNER JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            INNER JOIN FantasyChamp.Posição POS ON J.ID_Posição = POS.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 1
              AND POS.Posição = @Posicao;

            -- Se encontrou, promover para o campo
            IF @JogadorBancoPromover IS NOT NULL
            BEGIN
                UPDATE FantasyChamp.Pertence
                SET benched = 0
                WHERE ID_Equipa = @ID_Equipa
                  AND ID_Jogador = @JogadorBancoPromover;
            END
        END
    END

    COMMIT TRANSACTION;
END;
