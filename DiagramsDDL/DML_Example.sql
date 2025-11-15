-- Inserir o Estado do Jogador (caso não exista)
INSERT INTO FC_Estado_Jogador (ID, Estado)
VALUES ('EST01', 'Ativo');

-- Inserir o Clube (caso não exista)
INSERT INTO FC_Clube (ID, Nome, País)
VALUES ('CLUB01', 'Clube Exemplo', 'Portugal');

-- Inserir o Jogador
INSERT INTO FC_Jogador (ID, Nome, Posição, Preço, ID_clube, ID_Estado_Jogador)
VALUES ('JOG01', 'João Silva', 'Atacante', 1500000.00, 'CLUB01', 'EST01');
