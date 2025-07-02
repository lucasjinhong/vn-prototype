# ---- Base Stage ----
    FROM python:3.9-slim

    WORKDIR /app
    
    # ---- Build Stage ----
    COPY ../requirements.txt .
    
    ENV PATH="/home/app/.local/bin:${PATH}"
    RUN useradd -m app
    USER app
    
    RUN pip install --user --no-cache-dir -r requirements.txt
    
    COPY --chown=app:app . .
    
    # ---- Final Stage ----
    EXPOSE 5000
    
    # Use the real Gunicorn command again
    CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--config", "gunicorn.conf.py", "wsgi:app"]