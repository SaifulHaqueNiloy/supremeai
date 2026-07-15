import glob
import re

for path in glob.glob('tests/tools/test_*.py'):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace mock_acompletion.return_value = {\n            "text" 
    # with {"success": True, "text"
    new_content = re.sub(
        r'mock_acompletion\.return_value\s*=\s*\{\s*\"text\"',
        r'mock_acompletion.return_value = {\n            "success": True,\n            "text"',
        content
    )
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {path}')
