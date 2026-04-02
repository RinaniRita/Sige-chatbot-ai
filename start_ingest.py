import subprocess
import os
import sys

def start_ingest():
    """
    Convenience script to run the SIGE knowledge base ingestion from the root folder.
    This ensures all markdown files in SIGE_KB are chunked and indexed into the vector store.
    """
    print("🚀 Starting SIGE Knowledge Base Ingestion...")
    
    # Path to the .venv python executable
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        # fallback for linux/mac or local python if venv isn't found
        venv_python = "python"

    # Command to run the ingestion module
    cmd = [venv_python, "-m", "backend.data_scripts.ingest_sige"]
    
    try:
        # Run the command and stream output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Ingestion complete! The AI Consultant is now smarter.")
            print("💡 Reminder: You must restart the Telegram Bot to use the new information.")
        else:
            print(f"\n❌ Ingestion failed with exit code: {process.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error starting ingestion: {e}")

if __name__ == "__main__":
    start_ingest()
