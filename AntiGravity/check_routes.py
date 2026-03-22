import os
import re
from app import create_app

def main():
    app = create_app()

    template_dir = os.path.join('app', 'templates')
    # Coincide con url_for('endpoint' o "endpoint"
    url_for_pattern = re.compile(r"url_for\(['\"]([^'\"]+)['\"]")

    found_endpoints = set()
    for root, _, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = url_for_pattern.findall(content)
                    found_endpoints.update(matches)

    print('--- Found Endpoints in Templates ---')
    for ep in sorted(found_endpoints):
        print(ep)

    print('\n--- Checking against URL Map ---')
    valid_endpoints = set(rule.endpoint for rule in app.url_map.iter_rules())

    missing_endpoints = found_endpoints - valid_endpoints

    if missing_endpoints:
        print('\n!!! MISSING ROUTES !!!')
        for ep in sorted(missing_endpoints):
            print(ep)
    else:
        print('\nAll referenced routes exist!')

if __name__ == '__main__':
    main()
