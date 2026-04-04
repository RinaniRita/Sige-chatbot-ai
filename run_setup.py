import subprocess
import os

def run():
    # Use absolute paths to be safe (no matter where the command is triggered from)
    project_root = os.path.abspath(os.path.dirname(__file__))
    venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        # Fallback to system python if venv not found
        venv_python = "python"

    print(f"⚙️ Running SIGE Bot Setup (Greeting, Get Started, Menu)...")
    print(f"🐍 Using Python: {venv_python}")

    # Launching the setup tool from the tools directory
    cmd = [venv_python, "-m", "backend.tools.bot_setup"]
    
    try:
        # Run the command and set CWD to project root so 'backend' module is found
        subprocess.run(cmd, check=True, cwd=project_root)
        print("\n✅ Setup complete! Facebook Menu and Greeting have been updated.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run()
