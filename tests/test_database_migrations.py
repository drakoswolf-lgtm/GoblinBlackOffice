from sqlalchemy import create_engine, inspect, text

from app.core.migrations import upgrade_database
from app.core.models import Business
from app.core.sql_store import SqlBlackOfficeStore
from app.ledgergut.sql_storage import SqlReceiptStore


def test_initial_migration_creates_versioned_storage(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"

    upgrade_database(url)

    engine = create_engine(url, future=True)
    tables = set(inspect(engine).get_table_names())
    assert {"alembic_version", "office_records", "ledgergut_receipts"}.issubset(tables)
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "20260910_0001"


def test_sql_stores_share_idempotent_migrated_schema(tmp_path):
    url = f"sqlite:///{tmp_path / 'stores.db'}"

    office = SqlBlackOfficeStore(url)
    office.businesses.save(Business(business_id="BIZ-MIG", name="Migration Forge"))

    receipts = SqlReceiptStore(url, lambda: "BIZ-MIG")
    receipt_id = receipts.save_receipt(
        {"description": "Migration test", "receipt": {"vendor_name": "Forge Supply"}}
    )

    assert office.businesses.get("BIZ-MIG", "BIZ-MIG").name == "Migration Forge"
    assert receipts.list_receipts()[0]["record_id"] == receipt_id
