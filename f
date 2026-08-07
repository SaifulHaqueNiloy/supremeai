import os

BASE = r'f:\supremeai backup'

# Fix cryptography constraint in pyproject.toml
fn = os.path.join(BASE, 'backend/pyproject.toml')
with open(fn, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('cryptography = "^43.0.1"', 'cryptography = "^44.0.1"')
with open(fn, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done: pyproject.toml - updated cryptography constraint to ^44.0.1")

# Verify
with open(fn, 'r', encoding='utf-8') as f:
    verify = f.read()
if 'cryptography = "^44.0.1"' in verify:
    print("VERIFIED: cryptography constraint is now ^44.0.1")
else:
    print("ERROR: cryptography constraint was not changed!")
if 'litellm = "^1.91.0"' in verify:
    print("VERIFIED: litellm constraint is now ^1.91.0")
else:
    print("ERROR: litellm constraint was not changed!")
