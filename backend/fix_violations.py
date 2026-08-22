import os
import re

def fix_violations(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original = content
            
            # Replace `except Exception:\n    pass` with `except Exception as e:\n    logger.debug(e)`
            # We'll use a regex for this
            content = re.sub(
                r'except Exception:\s+pass',
                r'except Exception as e:\n            logger.debug(f"Error: {e}")',
                content
            )
            
            # Replace `except:\n    pass`
            content = re.sub(
                r'except:\s+pass',
                r'except Exception as e:\n            logger.debug(f"Error: {e}")',
                content
            )

            # Check if there are prints in backend logic (excluding CLI tool or tests)
            # Actually, just replace all `print(` with `logger.info(` if it's not a CLI script.
            # Some files have print statements with indentation. 
            # We must be careful not to replace prints in strings.
            # A simple regex for print at start of line or after whitespace
            if re.search(r'^\s*print\(', content, flags=re.MULTILINE):
                content = re.sub(r'^(\s*)print\(', r'\1logger.info(', content, flags=re.MULTILINE)

            if content != original:
                # Need to ensure logger is imported
                if 'from loguru import logger' not in content and 'import logging' not in content:
                    # Insert after the first docstring or at top
                    if content.startswith('"""'):
                        end_idx = content.find('"""', 3)
                        if end_idx != -1:
                            content = content[:end_idx+3] + '\nfrom loguru import logger\n' + content[end_idx+3:]
                        else:
                            content = 'from loguru import logger\n' + content
                    else:
                        content = 'from loguru import logger\n' + content
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Fixed {filepath}")

fix_violations('backend/core')
fix_violations('backend/api')
