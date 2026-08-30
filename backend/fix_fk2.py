file_path = "alembic_migrations/versions/j9k0l1m2n3o4_add_missing_live_model_tables.py"
with open(file_path, encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'sa.ForeignKeyConstraint(["execution_id"], ["automation_executions.id"], ondelete="CASCADE"),',
    "# removed FK",
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
