# Use uma imagem base do Python slim
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências
COPY requirements.txt.

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação para o diretório de trabalho
COPY..

# Expõe a porta que o Gunicorn irá rodar
EXPOSE 5000

# Comando para iniciar a aplicação usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]