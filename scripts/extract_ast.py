import os
import ast
import json

def extract_file_info(filepath):
    info = {
        'path': filepath,
        'docstring': '',
        'classes': [],
        'functions': [],
        'imports': [],
        'dependencies': [],
        'streamlit_calls': False,
        'ml_calls': False,
        'has_numpy': False
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return info
        
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return info
        
    info['docstring'] = ast.get_docstring(tree) or ''
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                info['imports'].append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                info['imports'].append(node.module)
        elif isinstance(node, ast.ClassDef):
            cls_info = {
                'name': node.name,
                'docstring': ast.get_docstring(node) or '',
                'methods': []
            }
            for cls_node in node.body:
                if isinstance(cls_node, ast.FunctionDef):
                    cls_info['methods'].append({
                        'name': cls_node.name,
                        'docstring': ast.get_docstring(cls_node) or ''
                    })
            info['classes'].append(cls_info)
        elif isinstance(node, ast.FunctionDef):
            # Check if it's a top level function
            if getattr(node, 'col_offset', -1) == 0:
                info['functions'].append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or ''
                })
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'st':
                        info['streamlit_calls'] = True
                if node.func.attr in ['predict', 'predict_proba', 'load', 'dump']:
                    info['ml_calls'] = True
    
    info['dependencies'] = list(set(info['imports']))
    info['has_numpy'] = 'numpy' in info['dependencies'] or 'pandas' in info['dependencies']
    return info

def main():
    src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
    all_info = []
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                all_info.append(extract_file_info(filepath))
                
    with open('ast_inventory.json', 'w', encoding='utf-8') as f:
        json.dump(all_info, f, indent=2)

if __name__ == '__main__':
    main()
