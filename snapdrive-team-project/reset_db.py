import os
import sqlite3

db_name = "snapdrive.db"
upload_folder = "uploads"

def reset_database():
    print(f"[*] Resetting SnapDrive system...")
    
    # Remove database file if it exists
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            print(f"[+] Database '{db_name}' deleted.")
        except Exception as e:
            print(f"[!] Error deleting database: {e}")
    else:
        print(f"[-] Database '{db_name}' not found.")

    # Clear uploads folder
    if os.path.exists(upload_folder):
        print(f"[*] Clearing uploads folder...")
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"    - Deleted: {filename}")
            except Exception as e:
                print(f"    [!] Error deleting {filename}: {e}")
    else:
        os.makedirs(upload_folder, exist_ok=True)
        print(f"[+] Created uploads folder.")

    print("\n[SUCCESS] SnapDrive has been reset. Tables will be recreated on next server start.")

if __name__ == "__main__":
    reset_database()

 