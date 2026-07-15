from __future__ import .*', content)
from __future__ import .*\n', '', content)
import os
import re

def fix():
    backend_dir = r'C:\Users\n\supremeai\supremeai_2.0\backend'
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'from __future__' in content and not content.lstrip().startswith('from __future__') and not content.lstrip().startswith('#') and not content.lstrip().startswith('\"\"\"'):
                    future_imports = re.findall(r'                    content = re.sub(r'                    content = '\n'.join(future_imports) + '\n' + content
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'Fixed __future__ in {filepath}')

if __name__ == '__main__':
    fix()
