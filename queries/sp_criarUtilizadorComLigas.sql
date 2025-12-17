CREATE OR ALTER PROCEDURE sp_CriarUtilizadorComLigas
    @PrimeiroNome NVARCHAR(100),
    @Apelido NVARCHAR(100),
    @Email NVARCHAR(255),
    @Senha NVARCHAR(255),
    @Pais NVARCHAR(100),
    @Nacionalidade NVARCHAR(100),
    @DataNascimento DATE,
    @UserID UNIQUEIDENTIFIER OUTPUT,
    @Sucesso BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    -- Inicializar outputs
    SET @UserID = NULL;
    SET @Sucesso = 0;
    SET @Mensagem = '';

    DECLARE @LigaMundialID UNIQUEIDENTIFIER;
    DECLARE @LigaPaisID UNIQUEIDENTIFIER;
    DECLARE @LigaTipoPublica VARCHAR(16) = 'LT01';

    -- VALIDAÇÕES ANTES DE ABRIR TRANSAÇÃO (evita transaction mismatch)
    
    -- Verificar email duplicado
    IF EXISTS (SELECT 1 FROM FantasyChamp.Utilizador WHERE Email = @Email)
    BEGIN
        SET @Mensagem = 'Email already exists';
        RETURN;
    END

    -- Verificar se o país existe na tabela de países
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pais WHERE Pais.nome = @Pais OR ID = @Pais)
    BEGIN
        SET @Mensagem = 'Invalid Country';
        RETURN;
    END

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Criar utilizador
        SET @UserID = NEWID();

        INSERT INTO FantasyChamp.Utilizador
            (ID, PrimeiroNome, Apelido, Email, Senha, País, Nacionalidade, DataDeNascimento)
        VALUES
            (@UserID, @PrimeiroNome, @Apelido, @Email, @Senha, @Pais, @Nacionalidade, @DataNascimento);

        -- 1) LIGA MUNDIAL
        -- Verificar se já existe liga Mundial
        SELECT @LigaMundialID = ID
        FROM FantasyChamp.Liga
        WHERE Nome = 'Mundial' AND ID_tipoLiga = @LigaTipoPublica;

        -- Se não existe, criar
        IF @LigaMundialID IS NULL
        BEGIN
            SET @LigaMundialID = NEWID();

            INSERT INTO FantasyChamp.Liga
                (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES
                (@LigaMundialID, 'Mundial', GETDATE(),
                CONVERT(DATE, '2026-05-30', 23),
                @LigaTipoPublica, '00000000-0000-0000-0000-000000000000', NULL);
        END

        -- Adicionar utilizador à Liga Mundial
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                      WHERE ID_Utilizador = @UserID AND ID_Liga = @LigaMundialID)
        BEGIN
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (@UserID, @LigaMundialID);
        END

        -- 2) LIGA DO PAÍS
        -- Verificar se já existe liga do país
        SELECT @LigaPaisID = ID
        FROM FantasyChamp.Liga
        WHERE Nome = 'Liga ' + @Pais AND ID_tipoLiga = @LigaTipoPublica;

        -- Se não existe, criar
        IF @LigaPaisID IS NULL
        BEGIN
            SET @LigaPaisID = NEWID();

            -- Obter código do país (pode ser diferente do nome)
            DECLARE @CodigoPais VARCHAR(16);
            SELECT TOP 1 @CodigoPais = ID
            FROM FantasyChamp.Pais
            WHERE Pais.nome = @Pais OR ID = @Pais;

            INSERT INTO FantasyChamp.Liga
                (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES
                (@LigaPaisID, 'Liga ' + @Pais, GETDATE(),
                CONVERT(DATE, '2026-05-30', 23),
                @LigaTipoPublica, '00000000-0000-0000-0000-000000000000', @CodigoPais);
        END

        -- Adicionar utilizador à Liga do País
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                      WHERE ID_Utilizador = @UserID AND ID_Liga = @LigaPaisID)
        BEGIN
            INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
            VALUES (@UserID, @LigaPaisID);
        END

        SET @Sucesso = 1;
        SET @Mensagem = 'Account created successfully';

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @Sucesso = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
        SET @UserID = NULL;
    END CATCH
END;