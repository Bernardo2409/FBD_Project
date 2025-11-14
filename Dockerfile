# Imagem base oficial do Python
FROM python:3.13-slim

# Instalar dependências do sistema para pyodbc e SQL Server ODBC driver
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get clean

# Baixar e instalar o driver ODBC para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

# Diretório da aplicação
WORKDIR /app

# Copiar todos os ficheiros do projeto para o container
COPY . .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta 5000 (padrão do Flask)
EXPOSE 5000

# Comando para arrancar o Flask
CMD ["python", "app.py"]
