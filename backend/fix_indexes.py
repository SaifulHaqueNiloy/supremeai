import re

path = "alembic_migrations/versions/k1l2m3n4o5p6_fix_downgrade_upgrade_table_swap.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

# Add get_indexes at the top of upgrade()
inspector_setup = """    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    existing_indexes = set()
    for table in existing_tables:
        for idx in inspector.get_indexes(table):
            existing_indexes.add(idx['name'])"""

content = content.replace(
    "    bind = op.get_bind()\n    inspector = sa.inspect(bind)\n    existing_tables = set(inspector.get_table_names())",
    inspector_setup,
)

# Pattern to find try-except blocks for create_index
pattern = re.compile(
    r'([ \t]+)try:\n([ \t]+)(op\.create_index\([^)]*op\.f\("([^"]+)"\)[^)]*\))\n[ \t]+except Exception:\n[ \t]+pass[ \t]*#?.*?\n',
    re.MULTILINE | re.DOTALL,
)


def replacer(match):
    indent = match.group(1)
    inner_indent = match.group(2)
    create_stmt = match.group(3)
    idx_name = match.group(4)
    # create the if condition
    return f'{indent}if "{idx_name}" not in existing_indexes:\n{inner_indent}{create_stmt}\n'


new_content = pattern.sub(replacer, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replaced try blocks:", len(pattern.findall(content)))
