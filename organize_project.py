import os
import shutil

def organize():
    # Current directory (Dr.MeD-AI)
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    print(f"📂 Organizing project in: {current_dir}")
    
    # List of files to move from parent to here
    files_to_move = ["API_DOCUMENTATION.md", ".env"]
    
    for filename in files_to_move:
        src = os.path.join(parent_dir, filename)
        dst = os.path.join(current_dir, filename)
        
        if os.path.exists(src):
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"✅ Imported {filename} to Dr.MeD-AI folder")
            else:
                print(f"ℹ️  {filename} already exists in Dr.MeD-AI folder")
        else:
            pass
            
    print("\n✨ Project is ready!")
    print("1. Close this terminal.")
    print(f"2. Move the '{os.path.basename(current_dir)}' folder to your Desktop.")
    print(f"3. You can then delete the '{os.path.basename(parent_dir)}' folder.")

if __name__ == "__main__":
    organize()