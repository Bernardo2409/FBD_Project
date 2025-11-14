# Imagem base oficial do Python
FROM python:3.13-slim

# Diretório da aplicação
WORKDIR /app

# Copiar todos os ficheiros do projeto para o container
COPY . .

# Instalar Flask
RUN pip install flask --no-cache-dir

# Flask usa a porta 5000
EXPOSE 5000

# Comando para arrancar o Flask
CMD ["python", "app.py"]
