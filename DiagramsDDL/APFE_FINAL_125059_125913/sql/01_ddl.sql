CREATE TABLE FantasyChamp.Utilizador (
	ID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
	PrimeiroNome VARCHAR(16) NOT NULL,
	Apelido VARCHAR(16) NOT NULL,
	Email VARCHAR(16) NOT NULL,
	Senha VARCHAR(16) NOT NULL,
	País VARCHAR(16),
	Nacionalidade VARCHAR(16) NOT NULL,
	DataDeNascimento VARCHAR(16)
);

CREATE TABLE FantasyChamp.Equipa (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Orçamento FLOAT(16) NOT NULL DEFAULT 100,
	Nome VARCHAR(16) NOT NULL,
	PontuaçãoTotal INT NOT NULL DEFAULT 0,
	ID_utilizador UNIQUEIDENTIFIER NOT NULL,

	FOREIGN KEY (ID_utilizador)
		REFERENCES FantasyChamp.Utilizador(ID)
);

-- NOVO

CREATE TABLE FantasyChamp.País (
    ID varchar(8) NOT NULL PRIMARY KEY,
    País varchar(30) NOT NULL,
    país_imagem varchar(100)
);

CREATE TABLE FantasyChamp.Clube (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Nome VARCHAR(16) NOT NULL,
	ID_País VARCHAR(16) NOT NULL,

	FOREIGN KEY (ID_País)
		REFERENCES FantasyChamp.País(ID)
);

CREATE TABLE FantasyChamp.Estado_Jogador (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Estado VARCHAR(16) NOT NULL
);

-- NOVO

CREATE TABLE FantasyChamp.Posição (
    ID varchar(8) NOT NULL PRIMARY KEY,
    Posição varchar(20) NOT NULL
);

CREATE TABLE FantasyChamp.Jogador (

	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Nome VARCHAR(16) NOT NULL,
	ID_Posição VARCHAR(8) NOT NULL,
	Preço Float(16) NOT NULL,
	ID_clube VARCHAR(8) NOT NULL,
	ID_Estado_Jogador VARCHAR(8) NOT NULL,

	FOREIGN KEY (ID_clube)
		REFERENCES FantasyChamp.Clube(ID),

	FOREIGN KEY (ID_Estado_Jogador)
		REFERENCES FantasyChamp.Estado_Jogador(ID),

	FOREIGN KEY (ID_Posição)
		REFERENCES FantasyChamp.Posiçãço(ID)
);

CREATE TABLE FantasyChamp.Tipo_Liga (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Tipo VARCHAR(16) NOT NULL,
	Código VARCHAR(8) NOT NULL
);

CREATE TABLE FantasyChamp.Liga (
	ID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
	Nome VARCHAR(16) NOT NULL,
	Data_Inicio DATE NOT NULL,
	Data_Fim DATE NOT NULL,
	ID_tipoLiga VARCHAR(8) NOT NULL,
	ID_criador UNIQUEIDENTIFIER NOT NULL,

	FOREIGN KEY (ID_criador)
		REFERENCES FantasyChamp.Utilizador(ID),
    FOREIGN KEY (ID_tipoLiga)
        REFERENCES FantasyChamp.Tipo_Liga(ID)
);

CREATE TABLE FantasyChamp.Jornada (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	Data_Inicio DATE NOT NULL,
	Data_Fim DATE NOT NULL,
	Numero INT NOT NULL,
	ID_liga UNIQUEIDENTIFIER NOT NULL,

	FOREIGN KEY (ID_liga)
		REFERENCES FantasyChamp.Liga(ID)

);

CREATE TABLE FantasyChamp.Pontuação_Equipa (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	ID_equipa VARCHAR(8) NOT NULL,
	ID_jornada VARCHAR(8) NOT NULL,
	Pontuação_Jornada INT NOT NULL,

	FOREIGN KEY (ID_equipa)
		REFERENCES FantasyChamp.Equipa(ID),

	FOREIGN KEY (ID_jornada)
		REFERENCES FantasyChamp.Jornada(ID)
)

CREATE TABLE FantasyChamp.Pontuação_Jogador (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	ID_jogador VARCHAR(8) NOT NULL,
	ID_jornada VARCHAR(8) NOT NULL,
	TempoJogo INT NOT NULL DEFAULT 0,
    GolosSofridos INT DEFAULT 0,
    Pontuacao_Jornada INT NOT NULL,
    Assistencias INT DEFAULT 0,
    CartoesAmarelos INT DEFAULT 0,
    CartoesVermelhos INT DEFAULT 0,

	FOREIGN KEY (ID_jogador)
		REFERENCES FantasyChamp.Jogador(ID),

	FOREIGN KEY (ID_jornada)
		REFERENCES FantasyChamp.Jornada(ID)
)

CREATE TABLE FantasyChamp.Jogo (
	ID VARCHAR(8) NOT NULL PRIMARY KEY,
	[Data] DATE NOT NULL,
	ID_Clube1 VARCHAR(8) NOT NULL,
	ID_CLube2 VARCHAR(8) NOT NULL,
	ID_jornada VARCHAR(8) NOT NULL,

	FOREIGN KEY (ID_Clube1)
		REFERENCES FantasyChamp.Clube(ID),

	FOREIGN KEY (ID_Clube2)
		REFERENCES FantasyChamp.Clube(ID),

	FOREIGN KEY (ID_jornada)
		REFERENCES FantasyChamp.Jornada(ID)
)

CREATE TABLE FantasyChamp.Pertence (
    ID_Jogador VARCHAR(8) NOT NULL,
    ID_Equipa VARCHAR(8) NOT NULL,
    PRIMARY KEY (ID_Jogador, ID_Equipa),
    FOREIGN KEY (ID_Jogador) REFERENCES FantasyChamp.Jogador(ID),
    FOREIGN KEY (ID_Equipa) REFERENCES FantasyChamp.Equipa(ID)
);

CREATE TABLE FantasyChamp.Participa (
    ID_Utilizador UNIQUEIDENTIFIER NOT NULL,
    ID_Liga UNIQUEIDENTIFIER NOT NULL,
    PRIMARY KEY (ID_Utilizador, ID_Liga),
    FOREIGN KEY (ID_Utilizador) REFERENCES FantasyChamp.Utilizador(ID),
    FOREIGN KEY (ID_Liga) REFERENCES FantasyChamp.Liga(ID)
);

CREATE TABLE FantasyChamp.Enfrenta (
	ID_Jogo VARCHAR(8) NOT NULL,
	ID_Clube1 VARCHAR(8) NOT NULL,
	ID_Clube2 VARCHAR(8) NOT NULL

	FOREIGN KEY (ID_JOGO)
		REFERENCES FantasyChamp.Jogo(ID),

	FOREIGN KEY (ID_Clube1)
		REFERENCES FantasyChamp.Clube(ID),

	FOREIGN KEY (ID_CLube2)
		REFERENCES FantasyChamp.Clube(ID)
)
