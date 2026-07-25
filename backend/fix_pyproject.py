with open("pyproject.toml", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_dev_deps = False
for line in lines:
    if line.strip().startswith("[tool.poetry.group.dev.dependencies]"):
        in_dev_deps = True
        new_lines.append(line)
        new_lines.append('pytest = "^8.0"\n')
        new_lines.append('pytest-asyncio = "^0.23"\n')
        new_lines.append('pytest-cov = "^5.0"\n')
        new_lines.append('pytest-mock = "^3.14.0"\n')
        new_lines.append('pytest-timeout = "^2.3.0"\n')
        new_lines.append('pytest-xdist = "^3.6.1"\n')
        new_lines.append('respx = "^0.21.1"\n')
        new_lines.append('pytest-md = "^0.2.0"\n')
        new_lines.append('typeguard = "^4.2"\n')
        continue
    elif line.strip().startswith("["):
        in_dev_deps = False

    if in_dev_deps:
        continue
    new_lines.append(line)

with open("pyproject.toml", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
