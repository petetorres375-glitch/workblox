"""
One-time backfill: grant existing users (who signed up before the
entitlements table existed) the same tool access they already have today,
so they aren't unexpectedly shown the mandatory tool picker on their next
login. Only brand-new signups after this runs should ever hit that picker.

Run once, manually, right after deploying the entitlements schema + gate,
before any new users can sign up under the new system:

    railway run python scripts/backfill_entitlements.py

Safe to re-run: only touches users who currently have zero entitlement
rows, so it will never overwrite a real self-service or admin-set selection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Tool, User, UserEntitlement
from app.services.entitlements import seed_tools, set_entitlements


def run():
    app = create_app()
    with app.app_context():
        seed_tools()  # make sure the 21 tools exist before referencing them

        personal_keys = {t.key for t in Tool.query.filter(Tool.app.in_(["personal", "both"])).all()}
        business_keys = {t.key for t in Tool.query.filter(Tool.app.in_(["business", "both"])).all()}

        users_with_entitlements = {
            row.user_id
            for row in UserEntitlement.query.with_entities(UserEntitlement.user_id).distinct()
        }

        all_users = User.query.all()
        backfilled = 0
        for user in all_users:
            if user.id in users_with_entitlements:
                continue
            target = set(personal_keys)
            if user.plan == "business":
                target |= business_keys
            set_entitlements(user.id, target, source="plan_default")
            backfilled += 1

        print(f"Backfilled {backfilled} user(s). "
              f"{len(all_users) - backfilled} already had entitlements and were left untouched.")


if __name__ == "__main__":
    run()
