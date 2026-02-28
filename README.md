# FBD Project - FantasyChamp

## Como usar o Fantasy-Champ

1. **Instale as dependências:**
	- Recomendado: use um ambiente virtual Python (ex: `venv` ou `poetry`).
	- Com `pip`:
	  ```bash
	  pip install -r requirements.txt
	  ```
	- Com `poetry`:
	  ```bash
	  poetry install
	  ```

2. **Configure a base de dados:**
	- Crie um ficheiro `conf.ini` na raiz do projeto (não está incluído no repositório por segurança).
	- Preencha com as suas credenciais:
	  ```ini
	  [database]
	  server = <servidor>,<porta>
	  name = <nome_db>
	  username = <utilizador>
	  password = <password>
	  ```

3. **Popule a base de dados (opcional):**
	- Se necessário, execute o script para popular a base de dados:
	  ```bash
	  python populate_db.py
	  ```

4. **Execute a aplicação:**
	- Comando padrão entre no caminho app/:
	  ```bash
	  python app.py
	  ```
	- A aplicação ficará disponível em `http://localhost:5000` ou conforme indicado no terminal.

## Alterar dados de entrada na base de dados

1. **Via scripts SQL:**
	- Utilize os scripts na pasta `queries/` ou `DiagramsDDL/` para criar, popular ou modificar tabelas e dados.
	- Exemplos:
	  - Para criar tabelas: use os scripts em `DiagramsDDL/`.
	  - Para triggers, views, procedures e udfs: use os scripts em `queries/`.
	- Execute os scripts no seu cliente SQL ou ferramenta de administração (ex: DBeaver, Azure Data Studio, etc).

2. **Via aplicação web:**
	- Algumas operações (criar equipa, adicionar jogadores, criar ligas, etc) podem ser feitas diretamente pela interface web após login.

## Instalar dependências

1. **Com pip:**
	```bash
	pip install -r requirements.txt
	```

2. **Com poetry:**
	```bash
	poetry install
	```

## Notas adicionais

- Certifique-se de que tem Python 3.9 ou superior instalado.
- Para dúvidas sobre endpoints ou funcionalidades, consulte o código em `app.py` ou a documentação dos scripts SQL.