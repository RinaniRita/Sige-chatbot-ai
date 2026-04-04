import subprocess
import os

def run():
    # Use absolute paths to be safe
    project_root = os.path.abspath(os.path.dirname(__file__))
    venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        # Alternative: check in current dir
        venv_python = "python" # Fallback to system python if venv not found

    print(f"🤖 Starting SIGE AI Bot (Facebook Messenger)...")
    print(f"🐍 Using Python: {venv_python}")

    # Launching the renamed Facebook bot server
    cmd = [venv_python, "-m", "backend.bot_server"]
    
    try:
        subprocess.run(cmd, check=True, cwd=project_root)
    except KeyboardInterrupt:
        print("\nStopping Bot...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
