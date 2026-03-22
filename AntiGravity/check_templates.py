import os
import re

def main():
    routes_dir = os.path.join('app', 'routes')
    template_dir = os.path.join('app', 'templates')
    
    # Coincide con render_template('ruta/al/template.html'
    render_pattern = re.compile(r"render_template\(['\"]([^'\"]+)['\"]")

    missing_templates = []
    
    # Recorrer rutas
    for root, _, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = render_pattern.findall(content)
                    for tmpl in matches:
                        tmpl_path = os.path.join(template_dir, tmpl)
                        if not os.path.exists(tmpl_path):
                            missing_templates.append((file, tmpl))

    if missing_templates:
        print('!!! MISSING TEMPLATES !!!')
        for file, tmpl in sorted(missing_templates):
            print(f'{file} references {tmpl}')
    else:
        print('All referenced templates exist!')

if __name__ == '__main__':
    main()
