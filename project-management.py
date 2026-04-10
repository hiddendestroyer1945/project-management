import os
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Any

# --- Constants & Global Styles ---
PROJECTS_DIR = "projects"
FONT_MAIN = ("Arial", 16)
FONT_BOLD = ("Arial", 16, "bold")
FONT_HEADER = ("Arial", 18, "bold")
FONT_WATERMARK = ("Arial", 40, "bold")

class ProjectManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Project Management Workflow")
        self.root.geometry("1200x800") # Increased for 16pt fonts
        
        # Persistence Config Initialization
        if not os.path.exists(PROJECTS_DIR):
            os.makedirs(PROJECTS_DIR)
            
        # Global ttk Styling for Treeview
        self.style = ttk.Style()
        self.style.configure("Treeview", font=FONT_MAIN, rowheight=45) # Increased height for 16pt
        self.style.configure("Treeview.Heading", font=FONT_BOLD)

        # Internal Data Store
        self.projects: Dict[str, Any] = self.load_all_projects()

        self.setup_background()
        self.setup_menu()

    def setup_background(self):
        """Sets up the large background text as a subtle watermark."""
        self.bg_label = tk.Label(
            self.root, 
            text="PROJECT MANAGEMENT PROGRAM", 
            font=FONT_WATERMARK, 
            fg="gray85" # Subtle light gray
        )
        self.bg_label.place(relx=0.5, rely=0.5, anchor="center")

    def setup_menu(self):
        menubar = tk.Menu(self.root, font=FONT_MAIN)
        file_menu = tk.Menu(menubar, tearoff=0, font=FONT_MAIN)
        file_menu.add_command(label="New", command=self.open_create_project_window)
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
        """Loads all projects from JSON files with error reporting and migration."""
        projects = {}
        if not os.path.exists(PROJECTS_DIR):
            return projects

        for filename in os.listdir(PROJECTS_DIR):
            if filename.endswith(".json"):
                p_id = filename[:-5]
                filepath = os.path.join(PROJECTS_DIR, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # Migration: If old structure (tasks at root), move to a default requirement
                        if "tasks" in data and "requirements" not in data:
                            print(f"[*] Migrating legacy project: {p_id}")
                            legacy_tasks = data["tasks"]
                            # Convert 1.0 columns (Running/Ended) to 2.0 (In Progress/Completed)
                            migrated_tasks = {
                                "Not Started": legacy_tasks.get("Not Started", []),
                                "In Progress": legacy_tasks.get("Running", []),
                                "Completed": legacy_tasks.get("Ended", [])
                            }
                            data["requirements"] = [{
                                "name": "General Tasks",
                                "type": "Basic",
                                "completed": False,
                                "tasks": migrated_tasks
                            }]
                            del data["tasks"]
                            
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
            messagebox.showerror("IO Error", f"Could not save project data: {e}", parent=self.root)

    # --- PROJECT MANAGEMENT ---

    def open_create_project_window(self):
        win = tk.Toplevel(self.root)
        win.title("New Project")
        win.geometry("600x400") # Increased
        win.grab_set() # Modal focus
        
        tk.Label(win, text="Project Name:", font=FONT_MAIN).grid(row=0, column=0, pady=15, padx=15)
        name_ent = tk.Entry(win, font=FONT_MAIN, width=25)
        name_ent.grid(row=0, column=1, padx=15)

        tk.Label(win, text="Start Date:", font=FONT_MAIN).grid(row=1, column=0, pady=15, padx=15)
        start_ent = tk.Entry(win, font=FONT_MAIN, width=25)
        start_ent.grid(row=1, column=1, padx=15)

        tk.Label(win, text="End Date:", font=FONT_MAIN).grid(row=2, column=0, pady=15, padx=15)
        end_ent = tk.Entry(win, font=FONT_MAIN, width=25)
        end_ent.grid(row=2, column=1, padx=15)

        def save():
            raw_name = name_ent.get().strip()
            if not raw_name:
                messagebox.showwarning("Input Error", "Project name cannot be empty", parent=win)
                return
            
            # Security Check: Prevent overwriting via traversal
            safe_name = self._sanitize_filename(raw_name)
            if safe_name in self.projects:
                messagebox.showerror("Conflict", f"A project named '{safe_name}' already exists.", parent=win)
                return

            self.projects[safe_name] = {
                "display_name": raw_name,
                "dates": (start_ent.get(), end_ent.get()),
                "requirements": [] # New hierarchical structure
            }
            self.save_project(safe_name)
            win.destroy()
            messagebox.showinfo("Success", f"Project '{safe_name}' Created", parent=self.root)
            self.open_requirements_page(safe_name)

        tk.Button(win, text="New", command=save, width=12, font=FONT_BOLD).grid(row=3, column=0, pady=25)
        tk.Button(win, text="Cancel", command=win.destroy, width=12, font=FONT_BOLD).grid(row=3, column=1, pady=25)

    def open_list_projects_window(self):
        list_win = tk.Toplevel(self.root)
        list_win.title("Project Manager")
        list_win.geometry("800x600") # Increased
        
        frame = tk.Frame(list_win)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        tk.Label(frame, text="Double-click to open Kanban Board", font=("Arial", 14, "italic")).pack(pady=10)
        
        # Increased Listbox Font & Size
        lb = tk.Listbox(frame, width=60, font=FONT_MAIN, fg="black", selectbackground="gray70")
        lb.pack(pady=10, fill="both", expand=True)
        for p in sorted(self.projects.keys()):
            lb.insert(tk.END, p)

        def delete_selected():
            selected = lb.curselection()
            if not selected: return
            p_name = lb.get(selected)
            if messagebox.askokcancel("Verify Delete", f"Confirm deletion of project '{p_name}'?\nThis cannot be undone.", parent=list_win):
                safe_name = self._sanitize_filename(p_name)
                filepath = os.path.join(PROJECTS_DIR, f"{safe_name}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                del self.projects[p_name]
                lb.delete(selected)

        def on_double_click(event):
            selected = lb.curselection()
            if selected:
                self.open_requirements_page(lb.get(selected))

        btn_frame = tk.Frame(list_win)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Delete Selected", command=delete_selected, fg="red", font=FONT_BOLD, width=15).pack(side="left", padx=15)
        tk.Button(btn_frame, text="Close", command=list_win.destroy, font=FONT_BOLD, width=15).pack(side="left", padx=15)
        
        lb.bind("<Double-Button-1>", on_double_click)

    # --- REQUIREMENTS MANAGEMENT ---

    def open_requirements_page(self, project_name):
        req_win = tk.Toplevel(self.root)
        req_win.title(f"Requirements - {project_name}")
        req_win.geometry("1000x700")

        frame = tk.Frame(req_win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="Double-click to open Tasks | Right-click for Options", font=("Arial", 14, "italic")).pack(pady=10)

        columns = ("Name", "Type")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("Name", text="Requirement Name")
        tree.heading("Type", text="Requirement Type")
        tree.column("Name", width=600)
        tree.column("Type", width=200)

        # Tag for coloring completed requirements green
        tree.tag_configure("completed", background="lightgreen")

        tree.pack(fill="both", expand=True)

        def refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            for idx, req in enumerate(self.projects[project_name]["requirements"]):
                tags = ("completed",) if req.get("completed", False) else ()
                tree.insert("", "end", iid=str(idx), values=(req["name"], req["type"]), tags=tags)

        refresh_tree()

        def show_req_context_menu(event):
            item_id = tree.identify_row(event.y)
            menu = tk.Menu(req_win, tearoff=0, font=FONT_MAIN)
            
            if item_id:
                tree.selection_set(item_id)
                idx = int(item_id)
                menu.add_command(label="Edit Requirement", command=lambda: self.add_edit_requirement_dialog(project_name, idx, refresh_tree))
                menu.add_command(label="Delete Requirement", command=lambda: self.delete_requirement(project_name, idx, refresh_tree))
                menu.add_command(label="Completed", command=lambda: self.toggle_requirement_completion(project_name, idx, refresh_tree))
            else:
                menu.add_command(label="New Requirement", command=lambda: self.add_edit_requirement_dialog(project_name, None, refresh_tree))
                menu.add_command(label="Edit Requirement", command=lambda: messagebox.showwarning("Selection", "Select a requirement first."))
                menu.add_command(label="Delete Requirement", command=lambda: messagebox.showwarning("Selection", "Select a requirement first."))
            
            menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", show_req_context_menu)
        tree.bind("<Double-Button-1>", lambda e: self.on_req_double_click(project_name, tree))

    def on_req_double_click(self, project_name, tree):
        selected = tree.selection()
        if selected:
            idx = int(selected[0])
            self.open_kanban_board(project_name, idx)

    def add_edit_requirement_dialog(self, project_name, req_idx, callback):
        win = tk.Toplevel(self.root)
        is_edit = req_idx is not None
        win.title("Edit Requirement" if is_edit else "New Requirement")
        win.geometry("500x350")
        win.grab_set()

        req_data = self.projects[project_name]["requirements"][req_idx] if is_edit else {}

        tk.Label(win, text="Name:", font=FONT_MAIN).grid(row=0, column=0, padx=20, pady=20)
        name_ent = tk.Entry(win, font=FONT_MAIN, width=30)
        name_ent.grid(row=0, column=1)
        name_ent.insert(0, req_data.get("name", ""))

        tk.Label(win, text="Type:", font=FONT_MAIN).grid(row=1, column=0, padx=20, pady=20)
        type_combo = ttk.Combobox(win, values=["Basic", "Key", "Functional", "Technical"], font=FONT_MAIN, state="readonly")
        type_combo.grid(row=1, column=1)
        type_combo.set(req_data.get("type", "Basic"))

        def save():
            name = name_ent.get().strip()
            if not name:
                messagebox.showwarning("Input Error", "Name is required.", parent=win)
                return
            
            new_req = {
                "name": name,
                "type": type_combo.get(),
                "completed": req_data.get("completed", False),
                "tasks": req_data.get("tasks", {"Not Started": [], "In Progress": [], "Completed": []})
            }

            if is_edit:
                self.projects[project_name]["requirements"][req_idx] = new_req
            else:
                self.projects[project_name]["requirements"].append(new_req)
            
            self.save_project(project_name)
            callback()
            win.destroy()

        tk.Button(win, text="OK", command=save, font=FONT_BOLD, width=10).grid(row=2, column=0, pady=40)
        tk.Button(win, text="Cancel", command=win.destroy, font=FONT_BOLD, width=10).grid(row=2, column=1, pady=40)

    def delete_requirement(self, project_name, req_idx, callback):
        if messagebox.askokcancel("Verify Delete", "Are you sure delete this requirement.", parent=self.root):
            self.projects[project_name]["requirements"].pop(req_idx)
            self.save_project(project_name)
            callback()

    def toggle_requirement_completion(self, project_name, req_idx, callback):
        req = self.projects[project_name]["requirements"][req_idx]
        req["completed"] = not req.get("completed", False)
        self.save_project(project_name)
        callback()

    # --- TASK MANAGEMENT (KANBAN BOARD) ---

    def open_kanban_board(self, project_name, req_idx):
        req_name = self.projects[project_name]["requirements"][req_idx]["name"]
        board = tk.Toplevel(self.root)
        board.title(f"Tasks: {req_name} ({project_name})")
        board.geometry("1400x800")

        columns = ["Not Started", "In Progress", "Completed"]
        board_trees = {}

        for i, col in enumerate(columns):
            frame = tk.Frame(board, bd=3, relief="groove")
            frame.place(relx=i/3, rely=0, relwidth=1/3, relheight=1)
            tk.Label(frame, text=col, font=FONT_HEADER, pady=15).pack()
            
            tree = ttk.Treeview(frame, columns=("Branch",), show="tree headings")
            tree.heading("#0", text="Task Name")
            tree.heading("Branch", text="Git Branch")
            tree.column("#0", width=250)
            tree.column("Branch", width=200)
            
            tree.pack(fill="both", expand=True, padx=5, pady=5)
            board_trees[col] = tree
            
            tree.bind("<Button-3>", lambda e, c=col: self.show_context_menu(e, c, project_name, req_idx, board_trees))
            tree.bind("<Double-Button-1>", lambda e, c=col: self.on_task_double_click(e, c, project_name, req_idx, board_trees))
            
            for task in self.projects[project_name]["requirements"][req_idx]["tasks"].get(col, []):
                tree.insert("", "end", text=task['name'], values=(task.get('branch', ''),))

    def show_context_menu(self, event, column_name, project_name, req_idx, board_trees):
        tree = board_trees[column_name]
        item_id = tree.identify_row(event.y)
        
        menu = tk.Menu(self.root, tearoff=0, font=FONT_MAIN)
        
        if item_id:
            tree.selection_set(item_id)
            menu.add_command(label="Edit Task", command=lambda: self.edit_task(column_name, project_name, req_idx, board_trees))
            menu.add_command(label="Delete Task", command=lambda: self.delete_task(column_name, project_name, req_idx, board_trees))
            menu.add_separator()
            menu.add_command(label="Create Note", command=lambda: self.open_note_editor(column_name, project_name, req_idx, board_trees))
            menu.add_command(label="Edit Note", command=lambda: self.open_note_editor(column_name, project_name, req_idx, board_trees))
            menu.add_command(label="Delete Note", command=lambda: self.delete_note(column_name, project_name, req_idx, board_trees))
            menu.add_separator()
            
            # Dynamic Move Options
            cols = ["Not Started", "In Progress", "Completed"]
            for c in cols:
                if c != column_name:
                    menu.add_command(label=f"Move to {c}", command=lambda target=c: self.move_task(column_name, target, project_name, req_idx, board_trees))
        else:
            menu.add_command(label="New Task", command=lambda: self.add_task(column_name, project_name, req_idx, board_trees))
            menu.add_command(label="Edit Task", command=lambda: messagebox.showwarning("Selection", "Select a task first.", parent=self.root))
            menu.add_command(label="Delete Task", command=lambda: messagebox.showwarning("Selection", "Select a task first.", parent=self.root))
        
        menu.post(event.x_root, event.y_root)

    def on_task_double_click(self, event, col, p_name, req_idx, board_trees):
        tree = board_trees[col]
        item_id = tree.identify_row(event.y)
        if not item_id: return
        # Force-select the clicked row BEFORE opening the editor
        tree.selection_set(item_id)
        self.open_note_editor(col, p_name, req_idx, board_trees)

    def delete_note(self, col, p_name, req_idx, board_trees):
        tree = board_trees[col]
        selected = tree.selection()
        if not selected: return
        task_name = tree.item(selected)['text']
        
        task_list = self.projects[p_name]["requirements"][req_idx]["tasks"][col]
        for t in task_list:
            if t['name'] == task_name:
                if 'note' in t: del t['note']
                self.save_project(p_name)
                messagebox.showinfo("Success", "Note deleted.", parent=self.root)
                break

    def open_note_editor(self, col, p_name, req_idx, board_trees):
        tree = board_trees[col]
        selected = tree.selection()
        if not selected: return
        # Safely retrieve the item id from the selection tuple
        item_id = selected[0]
        task_name = tree.item(item_id, 'text')
        
        task_obj = None
        for t in self.projects[p_name]["requirements"][req_idx]["tasks"][col]:
            if t['name'] == task_name:
                task_obj = t
                break
        
        if not task_obj: return
        
        win = tk.Toplevel(self.root)
        win.title(f"Note: {task_name}")
        win.geometry("860x680")
        # NOTE: No grab_set() — keeps the board window interactive

        # --- Top Toolbar (Style selector + Apply button) ---
        # MUST be packed first (top)
        toolbar = tk.Frame(win, pady=8, relief="ridge", bd=1)
        toolbar.pack(side="top", fill="x", padx=5, pady=(5, 0))

        tk.Label(toolbar, text="Style:", font=FONT_MAIN).pack(side="left", padx=10)
        style_cb = ttk.Combobox(
            toolbar,
            values=["Heading-1", "Heading-2", "Heading-3", "Heading-4", "Heading-5", "Normal"],
            font=FONT_MAIN,
            state="readonly",
            width=14
        )
        style_cb.pack(side="left", padx=10)
        style_cb.set("Normal")

        # --- Bottom Save/Close Bar ---
        # CRITICAL: pack the bottom bar BEFORE the expanding text_area.
        # If text_area is packed first with expand=True it consumes all space
        # and the button bar is pushed completely off screen.
        btn_frame = tk.Frame(win, pady=10, relief="ridge", bd=1)
        btn_frame.pack(side="bottom", fill="x", padx=5, pady=(0, 5))

        def save_note():
            content = text_area.get("1.0", "end-1c")
            tags_data = []
            for tag in ["Heading-1", "Heading-2", "Heading-3", "Heading-4", "Heading-5", "Normal"]:
                ranges = text_area.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    tags_data.append({
                        "tag":   tag,
                        "start": str(ranges[i]),
                        "end":   str(ranges[i + 1])
                    })
            task_obj["note"] = {"text": content, "tags": tags_data}
            self.save_project(p_name)
            messagebox.showinfo("Saved", f"Note for '{task_name}' saved.", parent=win)

        def close_note():
            win.destroy()

        tk.Button(btn_frame, text="Save Note", command=save_note,
                  font=FONT_BOLD, width=16, bg="#2ecc71", fg="white").pack(side="left", padx=15)
        tk.Button(btn_frame, text="Close", command=close_note,
                  font=FONT_BOLD, width=10).pack(side="left", padx=5)

        def apply_style():
            chosen = style_cb.get()
            try:
                for s in ["Heading-1", "Heading-2", "Heading-3", "Heading-4", "Heading-5", "Normal"]:
                    text_area.tag_remove(s, "sel.first", "sel.last")
                text_area.tag_add(chosen, "sel.first", "sel.last")
            except tk.TclError:
                messagebox.showwarning("No Selection", "Highlight text first, then apply a style.", parent=win)

        tk.Button(toolbar, text="Apply Style", command=apply_style, font=FONT_BOLD).pack(side="left", padx=10)

        # --- Text Editor (packed last so it fills the remaining middle space) ---
        text_area = tk.Text(win, font=("Arial", 16), wrap="word", undo=True, relief="sunken", bd=2)
        text_area.pack(side="top", fill="both", expand=True, padx=10, pady=8)

        # Configure all heading/normal tags
        text_area.tag_configure("Heading-1", font=("Arial", 26, "bold"))
        text_area.tag_configure("Heading-2", font=("Arial", 24, "bold"))
        text_area.tag_configure("Heading-3", font=("Arial", 22, "bold"))
        text_area.tag_configure("Heading-4", font=("Arial", 20, "bold"))
        text_area.tag_configure("Heading-5", font=("Arial", 18, "bold"))
        text_area.tag_configure("Normal",    font=("Arial", 16))

        # Load existing note data if present
        existing_note = task_obj.get("note", {})
        if existing_note.get("text"):
            text_area.insert("1.0", existing_note["text"])
            for tag_data in existing_note.get("tags", []):
                try:
                    text_area.tag_add(tag_data["tag"], tag_data["start"], tag_data["end"])
                except tk.TclError:
                    pass  # Ignore stale index positions from old saves

    def add_task(self, col, p_name, req_idx, board_trees):
        name = simpledialog.askstring("Task Setup", "Task Name:", parent=self.root)
        if not name: return
        branch = simpledialog.askstring("Task Setup", "Git Branch:", parent=self.root)
        
        task_data = {"name": name, "branch": branch or ""}
        self.projects[p_name]["requirements"][req_idx]["tasks"][col].append(task_data)
        board_trees[col].insert("", "end", text=name, values=(branch or "",))
        self.save_project(p_name)

    def delete_task(self, col, p_name, req_idx, board_trees):
        tree = board_trees[col]
        selected = tree.selection()
        if not selected: return
        
        if messagebox.askokcancel("Confirm", "Permanently delete this task?", parent=self.root):
            task_name = tree.item(selected)['text']
            self.projects[p_name]["requirements"][req_idx]["tasks"][col] = [t for t in self.projects[p_name]["requirements"][req_idx]["tasks"][col] if t['name'] != task_name]
            tree.delete(selected)
            self.save_project(p_name)

    def edit_task(self, col, p_name, req_idx, board_trees):
        tree = board_trees[col]
        selected = tree.selection()
        if not selected: return

        item = tree.item(selected)
        old_name = item['text']
        old_branch = item['values'][0]

        new_name = simpledialog.askstring("Edit Task", "Task Name:", parent=self.root, initialvalue=old_name)
        if not new_name: return
        
        new_branch = simpledialog.askstring("Edit Task", "Git Branch:", parent=self.root, initialvalue=old_branch)

        for t in self.projects[p_name]["requirements"][req_idx]["tasks"][col]:
            if t['name'] == old_name:
                t['name'] = new_name
                t['branch'] = new_branch or ""
        
        tree.item(selected, text=new_name, values=(new_branch or "",))
        self.save_project(p_name)

    def move_task(self, from_col, to_col, p_name, req_idx, board_trees):
        tree_from = board_trees[from_col]
        selected = tree_from.selection()
        if not selected: return

        item = tree_from.item(selected)
        task_name = item['text']
        task_branch = item['values'][0]
        
        task_list_from = self.projects[p_name]["requirements"][req_idx]["tasks"][from_col]
        try:
            task_obj = next(t for t in task_list_from if t['name'] == task_name)
            task_list_from.remove(task_obj)
            self.projects[p_name]["requirements"][req_idx]["tasks"][to_col].append(task_obj)
            
            tree_from.delete(selected)
            board_trees[to_col].insert("", "end", text=task_name, values=(task_branch,))
            self.save_project(p_name)
        except StopIteration:
            messagebox.showerror("Error", "Task object state inconsistent. Refresh Board.", parent=self.root)

if __name__ == "__main__":
    app_root = tk.Tk()
    app = ProjectManager(app_root)
    app_root.mainloop()