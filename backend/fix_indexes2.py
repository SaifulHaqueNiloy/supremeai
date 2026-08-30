import re

path = "alembic_migrations/versions/k1l2m3n4o5p6_fix_downgrade_upgrade_table_swap.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(
    r'([ \t]+)try:\n([ \t]+)(op\.create_index\([\s\S]+?op\.f\("([^"]+)"\)[\s\S]+?\))\n[ \t]+except Exception:\n[ \t]+pass[ \t]*#?.*?\n',
    re.MULTILINE,
)


def replacer(match):
    indent = match.group(1)
    inner_indent = match.group(2)
    create_stmt = match.group(3)
    idx_name = match.group(4)
    return f'{indent}if "{idx_name}" not in existing_indexes:\n{inner_indent}{create_stmt}\n'


new_content = pattern.sub(replacer, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replaced try blocks:", len(pattern.findall(content)))
