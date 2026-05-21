import os
import glob

workspace_root = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE"
os.chdir(workspace_root)

# Find all python scripts in scratch dirs
scripts = []
for d in ["scratch", "tower_kernel/scratch", "tower_core/scratch"]:
    scripts.extend(glob.glob(f"{d}/**/*.py", recursive=True))

for script in scripts:
    with open(script, "r") as f:
        content = f.read()
    
    modified = False
    new_content = content
    
    # We want to import os if we are going to use os.environ
    if f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}' in new_content:
        if "import os" not in new_content:
            new_content = "import os\n" + new_content
            
        # Replace exact absolute path
        abs_path = f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}"
        new_content = new_content.replace(f'"{abs_path}', 'f"{os.environ.get(\'TOWER_DATA_ROOT\', \f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}\')}')
        new_content = new_content.replace(f"'{abs_path}", 'f"{os.environ.get(\'TOWER_DATA_ROOT\', \f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}\')}')
        
        # Replace relative path
        new_content = new_content.replace('f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}', 'f"{os.environ.get(\'TOWER_DATA_ROOT\', \f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}\')}')
        new_content = new_content.replace("f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}", 'f"{os.environ.get(\'TOWER_DATA_ROOT\', \f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}\')}')
        
        # If we replaced inside an f-string that didn't have f prefix, it's now f"f{...}" which is fine, wait no.
        # It's better to just write the file back.
        
        # Fix f"f{ double f strings
        new_content = new_content.replace('f"{', 'f"{')
        new_content = new_content.replace("f'{", "f'{")
        new_content = new_content.replace('f"', 'f"')
        
        if content != new_content:
            with open(script, "w") as f:
                f.write(new_content)
            print(f"Updated {script}")

