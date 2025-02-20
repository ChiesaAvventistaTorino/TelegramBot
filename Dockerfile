# Usa un'immagine leggera di Python
FROM python:3.9

# Imposta la directory di lavoro
WORKDIR /app

# Copia tutti i file del progetto nel container
COPY . /app

# Installa le dipendenze necessarie
RUN pip install --no-cache-dir -r requirements.txt

# Comando per eseguire il tuo script Python
CMD ["python", "script_telegram.py"]
