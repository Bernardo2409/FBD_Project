CREATE OR ALTER PROCEDURE FantasyChamp.sp_CriarUtilizadorComLigas
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

    -- VALIDAÇÕES ANTES DE ABRIR TRANSAÇÃO
    -- Verificar email duplicado
    IF EXISTS (SELECT 1 FROM FantasyChamp.Utilizador WHERE Email = @Email)
    BEGIN
        SET @Mensagem = 'Email already exists';
        RETURN;
    END

    -- Verificar se a senha foi fornecida e não está vazia
    IF @Senha IS NULL OR LTRIM(RTRIM(@Senha)) = ''
    BEGIN
        SET @Mensagem = 'Password is required';
        RETURN;
    END

    -- Verificar se o país existe na tabela de países
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pais WHERE nome = @Pais OR ID = @Pais)
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
GO