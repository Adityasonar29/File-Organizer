import os
import random

def create_dummy_files():
    base_dir = "TEST_STAGING"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 1. Define what we want to create
    # (Category, Extension, Number of files)
    file_types = [
        ("docs", ".docx", 3),
        ("data", ".xlsx", 2),
        ("scans", ".pdf", 3),
        ("photos", ".jpg", 4),
        ("notes", ".txt", 2),
        ("mystery", ".xyz", 2), # This tests the 'Uncategorized' logic
    ]

    print(f"Creating test environment in: {os.path.abspath(base_dir)}")

    # 2. Create categorized files in a messy structure
    for folder_name, ext, count in file_types:
        # Create some in subfolders to test "Deep Search"
        subfolder = os.path.join(base_dir, f"old_{folder_name}")
        os.makedirs(subfolder, exist_ok=True)

        for i in range(count):
            file_path = os.path.join(subfolder, f"sample_{i}{ext}")
            with open(file_path, "w") as f:
                # Add random content so they have unique hashes initially
                f.write(f"This is dummy data for {folder_name} file number {i}")

    # 3. CREATE DUPLICATES (The Ultimate Test)
    # We will create 3 files with DIFFERENT names but EXACTLY the same content
    duplicate_content = "This content is exactly the same for hashing tests."
    dup_paths = [
        os.path.join(base_dir, "original_photo.png"),
        os.path.join(base_dir, "copy_of_photo.png"),
        os.path.join(base_dir, "whatsapp_received_image.png")
    ]
    
    for p in dup_paths:
        with open(p, "w") as f:
            f.write(duplicate_content)
    
    print("✅ Created 3 identical files (should result in 2 deletions).")

    # 4. Create an empty folder to test "Empty Folder Deletion"
    os.makedirs(os.path.join(base_dir, "Ghost_Folder/Empty_Inside"), exist_ok=True)
    print("✅ Created nested empty folders (should be deleted).")

    print("\n--- TEST DATA READY ---")
    print("1. Open your Automation Tool.")
    print("2. Select the 'TEST_STAGING' folder.")
    print("3. Turn on 'Deep Search'.")
    print("4. Click EXECUTE.")

if __name__ == "__main__":
    create_dummy_files()