with open("pyproject.toml", encoding="utf-8") as f:
    content = f.read()
content = content.replace('pybreaker = "^2.0.1"', 'pybreaker = "*"')
with open("pyproject.toml", "w", encoding="utf-8") as f:
    f.write(content)
