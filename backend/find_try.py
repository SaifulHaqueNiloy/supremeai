path = "alembic_migrations/versions/k1l2m3n4o5p6_fix_downgrade_upgrade_table_swap.py"
with open(path, encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "try:" in line:
        print(f"Line {i + 1}:\n" + "".join(lines[i : i + 6]))
