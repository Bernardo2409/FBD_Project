CREATE PROCEDURE sp_EquipaJornada
    @UserID UNIQUEIDENTIFIER,
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @PontuacaoTotal INT;
    DECLARE @EquipaExiste BIT = 0;

    BEGIN TRY
        -- Verificar se o utilizador tem permissão para ver esta equipa
        SELECT @EquipaExiste = 1
        FROM FantasyChamp.Equipa E
        WHERE E.ID = @ID_Equipa
          AND E.ID_utilizador = @UserID;

        IF @EquipaExiste = 0
        BEGIN
            SET @Resultado = 0;
            SET @Mensagem = 'You do not have permission to view this team';
            RETURN;
        END

        -- Verificar se a jornada existe
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
        BEGIN
            SET @Resultado = 0;
            SET @Mensagem = 'Round not found';
            RETURN;
        END

        -- Obter detalhes da equipa com pontuações
        EXEC sp_ObterEquipaComPontuacoes
            @ID_Equipa = @ID_Equipa,
            @ID_Jornada = @ID_Jornada,
            @PontuacaoTotal = @PontuacaoTotal OUTPUT,
            @Resultado = @Resultado OUTPUT,
            @Mensagem = @Mensagem OUTPUT;

        IF @Resultado = 0
            RETURN;

        -- Retornar também informações da jornada
        SELECT
            J.ID AS JornadaID,
            J.Numero AS JornadaNumero,
            J.Data_Inicio,
            J.Data_Fim,
            @PontuacaoTotal AS PontuacaoTotalEquipa
        FROM FantasyChamp.Jornada J
        WHERE J.ID = @ID_Jornada;

        SET @Resultado = 1;
        SET @Mensagem = 'Operation completed successfully';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;