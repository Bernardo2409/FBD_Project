CREATE FUNCTION FantasyChamp.fn_OrcamentoSuficiente
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Preco_Jogador DECIMAL(10,2)
)
RETURNS BIT
AS
BEGIN
    DECLARE @Orcamento DECIMAL(10,2);

    SELECT @Orcamento = ISNULL(Orçamento, 0)
    FROM FantasyChamp.Equipa
    WHERE ID = @ID_Equipa;

    RETURN CASE WHEN @Orcamento >= @Preco_Jogador THEN 1 ELSE 0 END;
END;