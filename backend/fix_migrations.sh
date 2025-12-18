#!/bin/bash
set -e

echo "🔧 Fixing database migrations..."

# 1. Check PostgreSQL
echo "1. Checking PostgreSQL..."
if ! sudo systemctl is-active postgresql > /dev/null 2>&1; then
    echo "   PostgreSQL not running. Starting..."
    sudo systemctl start postgresql
fi

# 2. Clean up alembic
echo "2. Cleaning up alembic..."
rm -rf alembic alembic.ini 2>/dev/null || true

# 3. Initialize alembic
echo "3. Initializing alembic..."
alembic init -t async alembic

# 4. Create proper alembic.ini with all required sections
echo "4. Creating proper alembic.ini..."
cat > alembic.ini << 'INI'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Use sync URL for Alembic (postgresql:// not postgresql+asyncpg://)
sqlalchemy.url = postgresql://cgraph_admin:1994Lks!Oliver2017.@localhost/cgraph_dev

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
INI

# 5. Create migration
echo "5. Creating migration..."
alembic revision --autogenerate -m "Initial schema"

# 6. Apply migration
echo "6. Applying migration..."
alembic upgrade head

echo "✅ Migration fix complete!"
