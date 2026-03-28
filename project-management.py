import os
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Any

# --- Constants ---
PROJECTS_DIR = "projects"

class ProjectManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Project Management Workflow")
        self.root.geometry("800x600")
        
        # Persistence Config Initialization
        if not os.path.exists(PROJECTS_DIR):
            os.makedirs(PROJECTS_DIR)
            
        # Internal Data Store
        self.projects: Dict[str, Any] = self.load_all_projects()

        self.setup_background()
        self.setup_menu()

    def setup_background(self):
        """Sets up the large background text as a subtle watermark."""
        self.bg_label = tk.Label(
            self.root, 
            text="PROJECT MANAGEMENT PROGRAM", 
            font=("Arial", 30, "bold"), 
            fg="gray80" # Standardized watermark color
        )
        self.bg_label.place(relx=0.5, rely=0.5, anchor="center")

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Create", command=self.open_create_project_window)
        file_menu.add_command(label="List", command=self.open_list_projects_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    # --- SECURITY & UTILS ---
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes strings to be used as safe filenames (Path Traversal protection)."""
        # Remove non-alphanumeric/spaces/hyphens/underscores
        sanitized = re.sub(r'[^\w\s-]', '', name).strip()
        # Cap length to prevent filesystem errors
        return sanitized[:50]

    # --- PERSISTENCE LOGIC ---
    
    def load_all_projects(self) -> Dict[str, Any]:
        """Loads all projects from JSON files with error reporting."""
        projects = {}
        if not os.path.exists(PROJECTS_DIR):
            return projects

        for filename in os.listdir(PROJECTS_DIR):
            if filename.endswith(".json"):
                # Use filename as project name fallback or load from data
                p_id = filename[:-5]
                filepath = os.path.join(PROJECTS_DIR, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        projects[p_id] = data
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[*] Critical: Skipping corrupt project file {filename}: {e}")
                except Exception as e:
                    print(f"[*] Unexpected error loading {filename}: {e}")
        return projects

    def save_project(self, name: str):
        """Saves a project's state to a sanitized JSON file."""
        if name not in self.projects:
            return

        safe_name = self._sanitize_filename(name)
        filepath = os.path.join(PROJECTS_DIR, f"{safe_name}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.projects[name], f, indent=4, sort_keys=True)
        except OSError as e:
            messagebox.showerror("IO Error", f"Could not save project data: {e}")

    # --- PROJECT MANAGEMENT ---

    def open_create_project_window(self):
        win = tk.Toplevel(self.root)
        win.title("Create Project")
        win.grab_set() # Modal focus
        
        tk.Label(win, text="Project Name:").grid(row=0, column=0, pady=5, padx=5)
        name_ent = tk.Entry(win)
        name_ent.grid(row=0, column=1, padx=5)

        tk.Label(win, text="Start Date:").grid(row=1, column=0, padx=5)
        start_ent = tk.Entry(win)
        start_ent.grid(row=1, column=1, padx=5)

        tk.Label(win, text="End Date:").grid(row=2, column=0, padx=5)
        end_ent = tk.Entry(win)
        end_ent.grid(row=2, column=1, padx=5)

        def save():
            raw_name = name_ent.get().strip()
            if not raw_name:
                messagebox.showwarning("Input Error", "Project name cannot be empty")
                return
            
            # Security Check: Prevent overwriting via traversal
            safe_name = self._sanitize_filename(raw_name)
            if safe_name in self.projects:
                messagebox.showerror("Conflict", f"A project named '{safe_name}' already exists.")
                return

            self.projects[safe_name] = {
                "display_name": raw_name,
                "dates": (start_ent.get(), end_ent.get()),
                "tasks": {"Not Started": [], "Running": [], "Ended": []}
            }
            self.save_project(safe_name)
            win.destroy()
            messagebox.showinfo("Success", f"Project '{safe_name}' Created")

        tk.Button(win, text="Create", command=save, width=10).grid(row=3, column=0, pady=10)
        tk.Button(win, text="Cancel", command=win.destroy, width=10).grid(row=3, column=1, pady=10)

    def open_list_projects_window(self):
        list_win = tk.Toplevel(self.root)
        list_win.title("Project Manager")
        
        frame = tk.Frame(list_win)
        frame.pack(pady=10, padx=10, fill="both", expand=True)

        tk.Label(frame, text="Double-click to open Kanban Board", font=("Arial", 9, "italic")).pack()
        
        lb = tk.Listbox(frame, width=60, font=("Courier", 10))
        lb.pack(pady=5, fill="both", expand=True)
        for p in sorted(self.projects.keys()):
            lb.insert(tk.END, p)

        def delete_selected():
            selected = lb.curselection()
            if not selected: return
            p_name = lb.get(selected)
            if messagebox.askokcancel("Verify Delete", f"Confirm deletion of project '{p_name}'?\nThis cannot be undone."):
                safe_name = self._sanitize_filename(p_name)
                filepath = os.path.join(PROJECTS_DIR, f"{safe_name}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                del self.projects[p_name]
                lb.delete(selected)

        def on_double_click(event):
            selected = lb.curselection()
            if selected:
                self.open_kanban_board(lb.get(selected))

        btn_frame = tk.Frame(list_win)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete_selected, fg="red").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Close", command=list_win.destroy).pack(side="left", padx=5)
        
        lb.bind("<Double-Button-1>", on_double_click)

    # --- TASK MANAGEMENT (KANBAN BOARD) ---

    def open_kanban_board(self, project_name):
        board = tk.Toplevel(self.root)
        board.title(f"Board: {project_name}")
        board.geometry("1000x600")

        columns = ["Not Started", "Running", "Ended"]
        self.tree_views = {}

        for i, col in enumerate(columns):
            frame = tk.Frame(board, bd=2, relief="groove")
            frame.place(relx=i/3, rely=0, relwidth=1/3, relheight=1)
            tk.Label(frame, text=col, font=("Arial", 12, "bold"), pady=5).pack()
            
            tree = ttk.Treeview(frame, columns=("Description"), show="tree headings")
            tree.heading("#0", text="Task Name")
            tree.heading("Description", text="Brief Description")
            tree.pack(fill="both", expand=True)
            self.tree_views[col] = tree
            
            tree.bind("<Button-3>", lambda e, c=col: self.show_context_menu(e, c, project_name))
            
            for task in self.projects[project_name]["tasks"][col]:
                tree.insert("", "end", text=task['name'], values=(task.get('desc', ''),))

    def show_context_menu(self, event, column_name, project_name):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="New Task", command=lambda: self.add_task(column_name, project_name))
        menu.add_command(label="Delete Task", command=lambda: self.delete_task(column_name, project_name))
        menu.add_command(label="Rename Task", command=lambda: self.rename_task(column_name, project_name))
        menu.add_separator()
        
        # Dynamic Move Options
        if column_name != "Running":
            menu.add_command(label="Move to Running", command=lambda: self.move_task(column_name, "Running", project_name))
        if column_name != "Ended":
            menu.add_command(label="Move to Ended", command=lambda: self.move_task(column_name, "Ended", project_name))
        
        menu.post(event.x_root, event.y_root)

    def add_task(self, col, p_name):
        name = simpledialog.askstring("Task Setup", "Task Name:")
        if not name: return
        desc = simpledialog.askstring("Task Setup", "Brief Description:")
        
        task_data = {"name": name, "desc": desc or ""}
        self.projects[p_name]["tasks"][col].append(task_data)
        self.tree_views[col].insert("", "end", text=name, values=(desc or "",))
        self.save_project(p_name)

    def delete_task(self, col, p_name):
        tree = self.tree_views[col]
        selected = tree.selection()
        if not selected: return
        
        if messagebox.askokcancel("Confirm", "Permanently delete this task?"):
            task_name = tree.item(selected)['text']
            # Improved Task lookup to avoid object mismatch
            self.projects[p_name]["tasks"][col] = [t for t in self.projects[p_name]["tasks"][col] if t['name'] != task_name]
            tree.delete(selected)
            self.save_project(p_name)

    def rename_task(self, col, p_name):
        tree = self.tree_views[col]
        selected = tree.selection()
        if not selected: return

        new_name = simpledialog.askstring("Rename", "Enter new task name:")
        if new_name:
            old_name = tree.item(selected)['text']
            # Object update
            for t in self.projects[p_name]["tasks"][col]:
                if t['name'] == old_name:
                    t['name'] = new_name
            tree.item(selected, text=new_name)
            self.save_project(p_name)

    def move_task(self, from_col, to_col, p_name):
        tree_from = self.tree_views[from_col]
        selected = tree_from.selection()
        if not selected: return

        item = tree_from.item(selected)
        task_name = item['text']
        task_desc = item['values'][0]
        
        # Atomic Data Move
        task_list_from = self.projects[p_name]["tasks"][from_col]
        try:
            task_obj = next(t for t in task_list_from if t['name'] == task_name)
            task_list_from.remove(task_obj)
            self.projects[p_name]["tasks"][to_col].append(task_obj)
            
            # GUI Update
            tree_from.delete(selected)
            self.tree_views[to_col].insert("", "end", text=task_name, values=(task_desc,))
            self.save_project(p_name)
        except StopIteration:
            messagebox.showerror("Error", "Task object state inconsistent. Refresh Board.")

if __name__ == "__main__":
    app_root = tk.Tk()
    app = ProjectManager(app_root)
    app_root.mainloop()