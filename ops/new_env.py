from pathlib import Path
import secrets

path = Path(".env")

if path.exists():
    raise SystemExit(".env już istnieje; nie nadpisano sekretów.")

db_password = secrets.token_hex(24)
rabbit_password = secrets.token_hex(24)

lines = [
    f"DJANGO_SECRET_KEY={secrets.token_hex(32)}",
    f"DB_PASSWORD={db_password}",
    f"POSTGRES_PASSWORD={secrets.token_hex(24)}",
    f"RABBIT_PASSWORD={rabbit_password}",
    f"CELERY_BROKER_URL=amqp://monitor:{rabbit_password}@rabbit:5672//",
]

with path.open("w", encoding="utf-8", newline="\n") as file:
    file.write("\n".join(lines) + "\n")

path.chmod(0o600)
print("Utworzono .env. Nie dodawaj go do Git.")