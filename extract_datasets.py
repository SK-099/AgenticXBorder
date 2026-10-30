import zipfile
import os

# Mapping zip archives to dedicated target folders
archives = {
    "FUNSD.zip": "funsd",
    "task1&2_test(361p)-20261029T203850Z-1-001.zip": "sroie_task1_2",
    "task3-test 347p)-20261029T203924Z-1-001.zip": "sroie_task3",
    "test-20261029T204335Z-1-001.zip": "cord"
}

print("Starting extraction of test dataset archives on D: drive...\n")

for zip_name, target_dir in archives.items():
    if os.path.exists(zip_name):
        print(f"Extracting '{zip_name}' into folder '{target_dir}'...")
        os.makedirs(target_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
            
        print(f"✅ Successfully extracted to '{target_dir}'\n")
    else:
        print(f"⚠️ Archive not found: '{zip_name}'\n")

print("All datasets extracted into clean folders!")