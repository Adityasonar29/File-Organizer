import os
import shutil
import sqlite3
import datetime
import hashlib
import tkinter as tk
import re
from tkinter import filedialog, messagebox, ttk

# --- 1. DATABASE COMPONENT ---
# --- 1. DATABASE COMPONENT (FIXED) ---
class LoggerDB:
    def __init__(self, db_name="organizer_logs.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Create table with the new schema
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS file_logs 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, original_path TEXT, new_path TEXT, file_type TEXT, timestamp DATETIME, source TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS processed_folders 
            (folder_path TEXT PRIMARY KEY, last_run DATETIME)''')
        
        # --- AUTO-MIGRATION FIX ---
        # Check if the 'source' column exists. If not, add it.
        try:
            self.cursor.execute("SELECT source FROM file_logs LIMIT 1")
        except sqlite3.OperationalError:
            # Column missing (Old DB detected). Add it now.
            print("Updating database schema...")
            self.cursor.execute("ALTER TABLE file_logs ADD COLUMN source TEXT")
            self.conn.commit()
        # ---------------------------

        self.conn.commit()

    def log_move(self, old_path, new_path, extension, source):
        self.cursor.execute("INSERT INTO file_logs (original_path, new_path, file_type, timestamp, source) VALUES (?, ?, ?, ?, ?)",
                           (old_path, new_path, extension, datetime.datetime.now(), source))
        self.conn.commit()

    def mark_folder_done(self, folder_path):
        self.cursor.execute("INSERT OR REPLACE INTO processed_folders VALUES (?, ?)", 
                           (os.path.abspath(folder_path), datetime.datetime.now()))
        self.conn.commit()

    def is_folder_processed(self, folder_path):
        self.cursor.execute("SELECT 1 FROM processed_folders WHERE folder_path = ?", (os.path.abspath(folder_path),))
        return self.cursor.fetchone() is not None

# --- 2. CORE LOGIC COMPONENT ---
class FileOrganizer:
    def __init__(self, db_logger):
        self.db = db_logger
        self.nested_map = {
            'Documents': {
                'PDF_Docs': ['.pdf'], 'Word_Docs': ['.doc', '.docx'],
                'Excel_Sheets': ['.xls', '.xlsx', '.csv'], 'PowerPoints': ['.ppt', '.pptx'],
                'Text_Files': ['.txt', '.rtf'], 'Ebooks': ['.epub', '.mobi']
            },
            'Images': {
                'JPG_Photos': ['.jpg', '.jpeg'], 'PNG_Images': ['.png'],
                'Vector_SVG': ['.svg'], 'Other_Images': ['.gif', '.bmp', '.webp']
            },
            'Media': {
                'Video': ['.mp4', '.mkv', '.mov', '.avi'],
                'Audio': ['.mp3', '.wav', '.flac', '.m4a']
            },
            'Archives': {
                'Compressed': ['.zip', '.rar', '.7z', '.tar', '.gz']
            }
        }
        self.stats = {"moved": 0, "deleted": 0, "saved_kb": 0, "skipped_folders": 0}
        self.seen_hashes = set()

    def calculate_hash(self, filepath):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    # --- NEW: ROBUST DATE INTELLIGENCE ENGINE ---
    def validate_calendar_date(self, year, month, day):
        """Strictly validates if a date exists (handles leap years & 30/31 days)."""
        try:
            if not (2000 <= year <= 2199): return False
            datetime.date(year, month, day)
            return True
        except ValueError:
            return False

    def extract_reliable_date(self, filepath):
        """
        Priority 1: Filename (IMG_YYYYMMDD_HHMMSS)
        Priority 2: Filename (Separated formats)
        Priority 3: File System Metadata (Fallback)
        """
        filename = os.path.basename(filepath)
        
        # --- PATTERN 1: CONTINUOUS STRING (Your IMG_20220809_... format) ---
        # Matches 8 digits starting with 20 or 21
        cont_match = re.search(r'(20\d{2}|21\d{2})(\d{2})(\d{2})', filename)
        if cont_match:
            y, m, d = map(int, cont_match.groups())
            if self.validate_calendar_date(y, m, d):
                month_name = datetime.date(y, m, 1).strftime('%B')
                return str(y), month_name, "Filename (Continuous)"

        # --- PATTERN 2: SEPARATED FORMATS (YYYY-MM-DD or DD-MM-YYYY) ---
        sep_match = re.search(r'(20\d{2}|21\d{2})[-_ .](\d{1,2})[-_ .](\d{1,2})', filename)
        if sep_match:
            y, m, d = map(int, sep_match.groups())
            if self.validate_calendar_date(y, m, d):
                month_name = datetime.date(y, m, 1).strftime('%B')
                return str(y), month_name, "Filename (ISO)"

        # --- PATTERN 3: DD-MM-YYYY or MM-DD-YYYY ---
        rev_match = re.search(r'(\d{1,2})[-_ .](\d{1,2})[-_ .](20\d{2}|21\d{2})', filename)
        if rev_match:
            p1, p2, y = map(int, rev_match.groups())
            # Try DD-MM-YYYY
            if self.validate_calendar_date(y, p2, p1):
                month_name = datetime.date(y, p2, 1).strftime('%B')
                return str(y), month_name, "Filename (DD-MM-YYYY)"
            # Try MM-DD-YYYY
            elif self.validate_calendar_date(y, p1, p2):
                month_name = datetime.date(y, p1, 1).strftime('%B')
                return str(y), month_name, "Filename (MM-DD-YYYY)"

        # --- FALLBACK: METADATA ---
        # This only runs if the filename has NO valid date
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt.strftime('%Y'), dt.strftime('%B'), "Metadata (OS)"

    def backup_folder(self, source, exclude_folders, progress_callback):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{source}_BACKUP_{timestamp}"
        exclude_paths = [os.path.abspath(p) for p in (exclude_folders or [])]
        
        files_to_backup = []
        for root, dirs, files in os.walk(source):
            if any(os.path.abspath(root).startswith(exc) for exc in exclude_paths):
                continue
            for f in files: files_to_backup.append(os.path.join(root, f))
        
        total = len(files_to_backup)
        for i, f_path in enumerate(files_to_backup):
            rel = os.path.relpath(f_path, source)
            dest = os.path.join(backup_path, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(f_path, dest)
            progress_callback(i + 1, total, f"Backing up: {os.path.basename(f_path)}")
        return backup_path

    def organize(self, source_dir, deep_search, use_date, exclude_folders, progress_callback):
        self.stats = {"moved": 0, "deleted": 0, "saved_kb": 0, "skipped_folders": len(exclude_folders)}
        exclude_paths = [os.path.abspath(p) for p in (exclude_folders or [])]
        
        all_files = []
        for root, dirs, files in os.walk(source_dir):
            curr = os.path.abspath(root)
            if not deep_search and curr != os.path.abspath(source_dir): continue
            if any(curr.startswith(exc) for exc in exclude_paths): continue
            for f in files:
                if f != "organizer_logs.db": all_files.append(os.path.join(root, f))

        total = len(all_files)
        for i, f_path in enumerate(all_files):
            try:
                # 1. Duplicate Check
                f_size = os.path.getsize(f_path)
                f_hash = self.calculate_hash(f_path)
                if f_hash in self.seen_hashes:
                    os.remove(f_path)
                    self.stats["deleted"] += 1
                    self.stats["saved_kb"] += f_size / 1024
                    continue
                self.seen_hashes.add(f_hash)

                # 2. Base Category Mapping
                _, ext_raw = os.path.splitext(f_path)
                ext = ext_raw.lower()
                
                parent_folder = "Others"
                sub_folder = ""
                found = False
                for p_dir, sub_dict in self.nested_map.items():
                    for s_dir, exts in sub_dict.items():
                        if ext in exts:
                            parent_folder = p_dir
                            sub_folder = s_dir
                            found = True; break
                    if found: break
                
                # 3. Path Construction with Intelligence
                if use_date:
                    # CALL THE NEW INTELLIGENCE ENGINE
                    year, month, src_type = self.extract_reliable_date(f_path)
                    # Structure: Source / Category / Subfolder / Year / Month
                    target_path = os.path.join(source_dir, parent_folder, sub_folder, year, month)
                    log_msg = f"Sorting ({src_type}): {os.path.basename(f_path)}"
                else:
                    target_path = os.path.join(source_dir, parent_folder, sub_folder)
                    log_msg = f"Sorting: {os.path.basename(f_path)}"
                    src_type = "Category Only"

                os.makedirs(target_path, exist_ok=True)
                dest = os.path.join(target_path, os.path.basename(f_path))
                
                if os.path.exists(dest):
                    dest = os.path.join(target_path, f"copy_{i}_{os.path.basename(f_path)}")

                # 4. METADATA PRESERVATION MOVE (Copy2 + Delete)
                shutil.copy2(f_path, dest) # Preserves creation/mod times
                os.remove(f_path)          # Deletes original
                
                self.db.log_move(f_path, dest, ext, src_type)
                self.stats["moved"] += 1
                progress_callback(i + 1, total, log_msg)
                
            except Exception as e: 
                print(f"Error processing {f_path}: {e}")
                continue

        self._clean_empty_folders(source_dir, exclude_paths)
        self.db.mark_folder_done(source_dir)
        return self.stats

    def _clean_empty_folders(self, path, exclude_list):
        for root, dirs, files in os.walk(path, topdown=False):
            if root == path or any(os.path.abspath(exc) in os.path.abspath(root) for exc in exclude_list): continue
            if not os.listdir(root): os.rmdir(root)

# --- 3. FRONT-END ---
class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Senior Automator Pro - Deterministic Engine")
        self.db = LoggerDB()
        self.engine = FileOrganizer(self.db)
        self.exclude_list = []
        self.setup_ui()

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        f = tk.Frame(self.root, padx=20, pady=20)
        f.grid(sticky="nsew")
        f.columnconfigure(0, weight=1)

        # Source
        tk.Label(f, text="Source Folder:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(f, textvariable=self.path_var)
        self.path_entry.grid(row=1, column=0, pady=5, padx=(0, 5), sticky="ew")
        tk.Button(f, text="Browse", command=self.browse_source).grid(row=1, column=1)

        # Exclusions
        tk.Label(f, text="Excluded Folders:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=(10,0))
        list_frame = tk.Frame(f)
        list_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        h_scroll = tk.Scrollbar(list_frame, orient='horizontal')
        h_scroll.pack(side='bottom', fill='x')
        self.listbox = tk.Listbox(list_frame, height=4, xscrollcommand=h_scroll.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        h_scroll.config(command=self.listbox.xview)

        btn_ex_f = tk.Frame(f)
        btn_ex_f.grid(row=4, column=0, columnspan=2, sticky='w', pady=5)
        tk.Button(btn_ex_f, text="+ Add Exclusion", command=self.add_ex).pack(side='left', padx=2)
        tk.Button(btn_ex_f, text="Clear Selected", command=self.remove_ex).pack(side='left', padx=2)

        # Options
        self.deep_var = tk.BooleanVar()
        tk.Checkbutton(f, text="Deep Search (Include Subfolders)", variable=self.deep_var).grid(row=5, column=0, sticky='w')
        
        self.date_var = tk.BooleanVar()
        tk.Checkbutton(f, text="Smart Date Sort (Prioritize Filename -> Metadata)", variable=self.date_var, fg="darkgreen", font=('Arial', 9, 'bold')).grid(row=6, column=0, sticky='w')

        self.status_label = tk.Label(f, text="Status: Ready", fg="blue")
        self.status_label.grid(row=7, column=0, columnspan=2, pady=(10,0))
        self.progress = ttk.Progressbar(f, orient='horizontal', mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=2, sticky="ew", pady=5)
        self.perc_label = tk.Label(f, text="0%")
        self.perc_label.grid(row=9, column=0, columnspan=2)

        tk.Button(f, text="EXECUTE AUTOMATION", bg="#2c3e50", fg="white", font=('Arial', 12, 'bold'), 
                  command=self.run, height=2).grid(row=10, column=0, columnspan=2, sticky="ew", pady=20)

    def browse_source(self):
        path = filedialog.askdirectory()
        if path: self.path_var.set(path); self.path_entry.xview_moveto(1)

    def remove_ex(self):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            self.exclude_list.pop(idx)
            self.listbox.delete(idx)
    
    def add_ex(self):
        current_source = self.path_var.get()
        start_dir = current_source if os.path.exists(current_source) else None
        folder = filedialog.askdirectory(initialdir=start_dir, title="Select Folder to Exclude")
        if folder and folder not in self.exclude_list:
            self.exclude_list.append(folder); self.listbox.insert(tk.END, folder)

    def update_progress(self, current, total, status):
        p = int((current/total)*100)
        self.progress['value'] = p
        self.perc_label.config(text=f"{p}%")
        self.status_label.config(text=f"Status: {status}")
        self.root.update_idletasks()

    def run(self):
        source = self.path_var.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Invalid path!"); return

        try:
            if self.db.is_folder_processed(source):
                if not messagebox.askyesno("Warning", "Folder already processed. Continue?"): return

            if messagebox.askyesno("Backup", "Create Backup?"):
                self.engine.backup_folder(source, self.exclude_list, self.update_progress)

            stats = self.engine.organize(source, self.deep_var.get(), self.date_var.get(), self.exclude_list, self.update_progress)
            
            report = (f"Organization Complete!\n\n✅ Files Moved: {stats['moved']}\n"
                      f"🗑️ Duplicates Deleted: {stats['deleted']}\n💾 Space Saved: {stats['saved_kb']:.2f} KB")
            messagebox.showinfo("Summary Report", report)
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk(); app = OrganizerApp(root); root.mainloop()