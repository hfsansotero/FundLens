"""One-off: set isin on existing fund rows from config/funds.yaml (run once per DB)."""

import yaml
from sqlalchemy import text

from config.settings import settings
from fundlens.storage.database import get_session

funds = yaml.safe_load(open(settings.funds_config))["funds"]

with get_session() as s:
    for f in funds:
        if f.get("isin"):
            s.execute(
                text("UPDATE funds SET isin = :isin WHERE ticker = :ticker AND isin IS NULL"),
                {"isin": f["isin"], "ticker": f["ticker"]},
            )
    s.commit()

print("isin backfill done")
