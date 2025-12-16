ALTER PROCEDURE FantasyChamp.RemoverJogadorEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jogador varchar(16)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Preco_Jogador DECIMAL(10,2);

    BEGIN TRANSACTION;

    -- Obter preço do jogador
    SELECT @Preco_Jogador = J.Preço
    FROM FantasyChamp.Jogador J
    INNER JOIN FantasyChamp.Pertence P ON J.ID = P.ID_Jogador
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
    END

    COMMIT TRANSACTION;
END;