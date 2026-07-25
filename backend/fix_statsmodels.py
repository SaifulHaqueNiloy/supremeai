
with open("pyproject.toml", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("statsmodels = \"^0.15.0\"", "statsmodels = \"*\"")
with open("pyproject.toml", "w", encoding="utf-8") as f:
    f.write(content)

