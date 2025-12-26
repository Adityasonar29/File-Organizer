# Smart File Organizer Pro (Deterministic Engine)

To make your GitHub repository look professional, your README should clearly explain the **Date Priority System** we built. It shows potential users (and employers) that the code is deterministic and reliable.

Here is the updated `README.md`. I have included a section on the folder structure and how the "Intelligence Engine" handles those tricky camera filenames.

---

**Markdown**

```
# Smart File Organizer Pro (Deterministic Engine)

A high-performance Python utility with a GUI that organizes cluttered directories into a structured hierarchy based on file categories and smart date extraction.

## 🧠 The Intelligence Engine
Unlike basic organizers that only look at "Date Modified," this tool uses a **Deterministic Priority System** to find the most accurate timestamp:

1.  **Filename Analysis (Highest Priority):** Scans for `IMG_20220809` or `2022-08-09` patterns.
2.  **Strict Calendar Validation:** Uses real Gregorian calendar logic. It won't accept "Month 13" or "February 30."
3.  **Century Gatekeeping:** Only accepts years between `2000` and `2199` to avoid misidentifying random numbers in filenames.
4.  **Metadata Fallback:** If no date is found in the name, it uses the OS file system metadata while preserving original timestamps during the move.

## 📂 Project Structure
```text
file_organizer/
├── bin/
│   └── FileOrganizer.bat    # Quick-launch script (Windows)
├── src/
│   └── main.py              # Core Python application
├── requirements.txt         # (Standard Library Only)
└── README.md
```

## 🚀 Getting Started

### Prerequisites

* Python 3.x installed and added to your System PATH.

### Installation & Usage

1. Clone this repository:
   **Bash**

   ```
   git clone [https://github.com/YOUR_USERNAME/file-organizer-pro.git](https://github.com/YOUR_USERNAME/file-organizer-pro.git)
   ```
2. Navigate to the `bin` folder and double-click `FileOrganizer.bat`.
3. Select your **Source Folder**.
4. Check **"Smart Date Sort"** to enable the deterministic engine.
5. Click **EXECUTE AUTOMATION**.

---

### Access from Anywhere (CLI Integration)

You can launch the organizer from any folder in your Command Prompt by adding the `bin` folder to your Windows Environment Variables:

1. Copy the full path to the `bin` folder (e.g., `C:\Users\Name\file_organizer\bin`).
2. Search for **"Edit the system environment variables"** in Windows.
3. Click **Environment Variables** > Find **Path** in 'User variables' > Click **Edit**.
4. Click **New** and paste the path to your `bin` folder.
5. **Restart your CMD.** Now, simply type `FileOrganizer` from any directory to launch the tool!

## 🛠️ Features

* **Deterministic Sorting:**`Category > Subfolder > Year > Month`.
* **Duplicate Prevention:** Uses MD5 hashing to delete identical files and save space.
* **Metadata Preservation:** Uses `shutil.copy2` to ensure "Date Created" stays original.
* **SQLite Logging:** Every file move is logged in `organizer_logs.db` for traceability.
* **Deep Search:** Option to include or exclude subdirectories.

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

```

---

### Tips for your GitHub Upload:
1. **Add a Screenshot:** People love visuals. Take a screenshot of the Tkinter window and save it as `screenshot.png` in your root folder, then add `![App Screenshot](screenshot.png)` to the README.
2. **The `.gitignore`:** Make sure you still have that `.gitignore` file from before so your `organizer_logs.db` doesn't get uploaded to the public.



**Would you like me to help you write a `LICENSE` file (like the MIT License) to include in your repository?**
```


An intelligent, GUI-based file organization tool that uses a high-priority deterministic engine to sort files by Category and Date.

## 🚀 Features

- **Smart Date Extraction:** Prioritizes filename patterns (`YYYYMMDD`) before falling back to metadata.
- **Calendar Validation:** Strictly validates real dates (leap years, 30/31-day months).
- **Metadata Preservation:** Uses `shutil.copy2` to ensure original "Date Created" stamps are kept.
- **SQLite Logging:** Tracks every move for potential rollback or auditing.
- **Duplicate Detection:** MD5 hashing prevents moving duplicate files.

## 📁 Organization Structure

The tool organizes files into the following hierarchy:
`Source / Category / Subfolder / Year / Month`

## 🛠️ Usage

1. Clone the repo: `git clone https://github.com/YOUR_USERNAME/repo-name.git`
2. Run the script: `python src/main.py`
3. Select your source directory and hit **Execute Automation**.

## ⚖️ License

MIT License
