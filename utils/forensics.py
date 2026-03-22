import hashlib
import os
import datetime

def hash_file(filepath):
    """Generate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Error: {e}"

def log_chain_of_custody(filepath, dumps_dir):
    """Log the SHA-256 hash of the extracted file to chain_of_custody.log."""
    if not os.path.exists(dumps_dir):
        os.makedirs(dumps_dir)
        
    log_file = os.path.join(dumps_dir, "chain_of_custody.log")
    file_hash = hash_file(filepath)
    timestamp = datetime.datetime.now().isoformat()
    filename = os.path.basename(filepath)
    
    log_entry = f"[{timestamp}] FILE: {filename} | SHA-256: {file_hash}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    return file_hash
