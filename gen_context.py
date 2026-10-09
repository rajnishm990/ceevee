import os

# Configuration: Add extensions you want to include
EXTENSIONS = ('.py', '.js', '.ts', '.html', '.css', '.ipynb', '.csv', '.sql')
# Directories to skip to keep the context clean
EXCLUDE_DIRS = {'__pycache__', '.git', '.venv', 'node_modules', 'venv', 'dist', 'build'}

def generate_context():
    output_file = "project_context.md"
    project_root = os.getcwd()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Project Context: {os.path.basename(project_root)}\n\n")
        f.write("## Project Structure\n```text\n")
        
        # 1. Generate a quick tree-view for the agent to understand the hierarchy
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            level = root.replace(project_root, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                if file.endswith(EXTENSIONS) and file != output_file and file != os.path.basename(__file__):
                    f.write(f"{sub_indent}{file}\n")
        
        f.write("```\n\n---\n\n## File Contents\n\n")

        # 2. Extract code with proper headers and Markdown blocks
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith(EXTENSIONS) and file != output_file and file != os.path.basename(__file__):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, project_root)
                    
                    f.write(f"### File: {relative_path}\n")
                    f.write(f"**Path:** `{relative_path}`\n\n")
                    
                    # Detect language for the markdown block
                    lang = file.split('.')[-1] if '.' in file else ""
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as code_file:
                            content = code_file.read()
                            f.write(f"```{lang}\n{content}\n```\n\n")
                    except Exception as e:
                        f.write(f"*Error reading file: {str(e)}*\n\n")
                    
                    f.write("---\n")

    print(f"Context successfully generated in {output_file}")

if __name__ == "__main__":
    generate_context()