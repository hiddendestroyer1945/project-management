# Project Management Workflow

A professional, local-first Kanban tool for managing multiple projects and workflows. Built with Python and Tkinter, it provides a persistent, secure, and intuitive desktop environment for organizing tasks.

## 🚀 Features

-   **Multi-Project Support**: Create, manage, and switch between multiple independent projects.
-   **Dynamic Kanban Board**: Organize tasks across three core stages: *Not Started*, *Running*, and *Ended*.
-   **Local Persistence**: All project data is stored locally in sanitized JSON files.
-   **Context-Aware Menus**: Right-click on any task to rename, delete, or move it between different stages.
-   **Clean GUI Design**: Built with Tkinter's themed widgets (`ttk`) for a modern desktop experience.

## 📋 Technical Features

-   **Atomic Persistence Layer**: Every UI action (moving a task, renaming, etc.) is instantly synchronized to the filesystem to prevent data loss.
-   **Security-Hardened Input**: Implements a robust Regex-based sanitization engine to prevent **Path Traversal** and ensure legal filename mapping.
-   **Type-Safe Architecture**: Utilizes Python's `typing` module for enhanced maintainability and error-free task handling.
-   **Modular Workflow**: Designed as a standalone utility with zero external library dependencies beyond the standard Python installation (and `tk` for GUI).

## 🛠️ Prerequisites (Debian/Linux)

Ensure your system has the following packages installed:

-   `git`, `python3`, `python3-pip`, `python3-venv`, `python3-tk`

## 💻 Installation & Setup

Follow these steps to deploy the application on your Debian-based system:

### 1. Install System Dependencies
```bash
sudo apt update && sudo apt install git python3 python3-pip python3-venv python3-tk -y
```

### 2. Clone the Repository
```bash
git clone https://github.com/hiddendestroyer1945/project-management.git
cd project-management/
```

### 3. Initialize Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 4. Run the Application
```bash
python3 project-management.py
```

## 📖 Power User Features

-   **Filename Sanitization**: Any project name you enter is automatically passed through a `_sanitize_filename` filter. Illegal characters like `/`, `\`, and `..` are stripped to maintain system integrity.
-   **Project Recovery**: The `projects/` directory stores each project as a human-readable `.json` file. Data can be backed up or edited manually if required.

## License

This program is released under the GNU General Public License v3.0 (GPL-3.0).

---

**Author**: [hiddendestroyer1945](https://github.com/hiddendestroyer1945)
