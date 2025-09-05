#!/usr/bin/env bash
set -euo pipefail

# deploy_to_server.sh
# Uso: ejecutar en el servidor desde /home/carlos/gestion-alumnos
# Hace: backup DB, actualiza desde git o descomprime tarball, instala deps, aplica alembic, recarga gunicorn.

APP_DIR="/home/carlos/gestion-alumnos"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="/tmp/backup_$(date +%F_%H%M%S)"
GIT_BRANCH="main"
TARBALL_PATH="/tmp/proyecto_sanitizado.tgz"

echo "Deploy script starting at $(date)"
mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

# 1) Backup DB and app minimal copy
if [ -f instance/formacion.db ]; then
  echo "Backing up database to $BACKUP_DIR"
  cp instance/formacion.db "$BACKUP_DIR/formacion.db.bak"
fi

echo "Creating app archive backup"
tar czf "$BACKUP_DIR/app_backup_$(date +%F_%H%M%S).tgz" instance/ mi_plataforma_formacion_app/ || true

# 2) Update source
if [ -d .git ]; then
  echo "Updating from git (branch $GIT_BRANCH)"
  git fetch --all
  git checkout "$GIT_BRANCH" || true
  git pull origin "$GIT_BRANCH"
else
  if [ -f "$TARBALL_PATH" ]; then
    echo "No git repo found. Extracting tarball $TARBALL_PATH"
    tar xzf "$TARBALL_PATH" -C "$APP_DIR"
  else
    echo "No .git and no tarball found at $TARBALL_PATH. Aborting." 1>&2
    exit 2
  fi
fi

# 3) Virtualenv and deps
if [ -d "$VENV_DIR" ]; then
  echo "Activating virtualenv $VENV_DIR"
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  if [ -f requirements.txt ]; then
    echo "Installing requirements"
    pip install -r requirements.txt
  fi
else
  echo "Virtualenv not found at $VENV_DIR — skipping pip install"
fi

# 4) Apply DB migrations if alembic present
if [ -f alembic.ini ]; then
  if command -v alembic >/dev/null 2>&1; then
    echo "Applying alembic migrations"
    alembic upgrade head
  else
    echo "alembic not found in PATH. Skipping migrations."
  fi
fi

# 5) Reload Gunicorn: try HUP to master, otherwise restart
# Find master PID (the parent gunicorn process)
MASTER_PID=$(ps aux | egrep "gunicorn.*run:app" | egrep -v egrep | awk '{print $2}' | head -n1 || true)
if [ -n "$MASTER_PID" ]; then
  echo "Sending HUP to Gunicorn master PID $MASTER_PID"
  kill -HUP "$MASTER_PID"
  echo "Sent HUP. Gunicorn should gracefully reload workers."
else
  echo "Gunicorn master PID not found. Starting Gunicorn using recommended command." 
  if [ -d "$VENV_DIR" ]; then
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
  fi
  echo "Starting gunicorn..."
  nohup "$VENV_DIR/bin/gunicorn" --chdir "$APP_DIR" run:app -b 127.0.0.1:8000 --workers 1 --log-file - >/dev/null 2>&1 &
  echo "Gunicorn started (background)."
fi

echo "Deploy finished at $(date)"
exit 0
