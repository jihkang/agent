import os
from utils.util import safe_import, check_file
from utils.env import load_dotenv

def install_local_llm():
    load_dotenv()
    hugginface_hub = safe_import("huggingface_hub")
    
    repo_id = os.getenv("LOCAL_MODEL")                      # ex: TheBloke/Llama-2-13B-chat-GGUF
    model_file_name = os.getenv("LOCAL_MODEL_NAME")         # ex: llama-2-13b-chat.Q4_K_M.gguf
    local_dir = os.getenv("LOCAL_DIR")                      # ex: /Users/yourname/models/

    target_path = os.path.join(local_dir, os.path.join(repo_id, model_file_name))    
    if check_file(target_path):
        return

    hugginface_hub.snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        allow_patterns=[model_file_name]
    )
    

if __name__ == "__main__":
    install_local_llm()