from celery import Task
from datetime import datetime
import zipfile
import json
import os
from app.celery_app import celery_app
from app.core.database import get_db
from app.core.config import settings
from sqlalchemy import text


@celery_app.task(bind=True)
def backup_daily(self):
    """Ежедневное резервное копирование данных"""
    try:
        db = next(get_db())
        backup_date = datetime.now().strftime("%Y-%m-%d")
        backup_dir = "/app/backups"
        backup_file = os.path.join(backup_dir, f"export-{backup_date}.zip")

        # Создаем директорию для бэкапов
        os.makedirs(backup_dir, exist_ok=True)

        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Экспорт игр
            games_data = export_table(db, "game")
            zipf.writestr("games.ndjson", "\n".join([json.dumps(game) for game in games_data]))

            # Экспорт магазинов
            stores_data = export_table(db, "store")
            zipf.writestr("stores.ndjson", "\n".join([json.dumps(store) for store in stores_data]))

            # Экспорт событий
            events_data = export_table(db, "listing_event")
            zipf.writestr("listing_events.ndjson", "\n".join([json.dumps(event) for event in events_data]))

            # Экспорт истории цен
            price_history_data = export_table(db, "price_history")
            zipf.writestr("price_history.ndjson", "\n".join([json.dumps(price) for price in price_history_data]))

            # Экспорт правил
            rules_data = export_table(db, "alert_rule")
            zipf.writestr("alert_rules.json", json.dumps(rules_data, indent=2, default=str))

            # Экспорт агентов
            agents_data = export_table(db, "source_agent")
            zipf.writestr("sources.json", json.dumps(agents_data, indent=2, default=str))

            # Метаданные бэкапа
            backup_metadata = {
                "schema": "1.0",
                "created_at": datetime.now().isoformat(),
                "tables": ["game", "store", "listing_event", "price_history", "alert_rule", "source_agent"]
            }
            zipf.writestr("version.json", json.dumps(backup_metadata, indent=2))

        return {
            "status": "success",
            "backup_file": backup_file,
            "backup_date": backup_date,
            "size_bytes": os.path.getsize(backup_file)
        }

    except Exception as exc:
        self.retry(exc=exc, countdown=3600, max_retries=3)


def export_table(db, table_name):
    """Экспорт таблицы в формате JSON"""
    query = text(f"SELECT * FROM {table_name}")
    result = db.execute(query)

    # Конвертация строк в словари
    columns = result.keys()
    rows = []
    for row in result:
        row_dict = dict(zip(columns, row))
        # Конвертация UUID и datetime в строки
        for key, value in row_dict.items():
            if hasattr(value, 'isoformat'):
                row_dict[key] = value.isoformat()
            elif hasattr(value, '__str__'):
                row_dict[key] = str(value)
        rows.append(row_dict)

    return rows