# Dependencies:
# Required:
# - pandas: For CSV parsing and data handling
#   Install with: pip install pandas
# - tkinter: Built-in with Python 3.11, no installation needed
# Optional (not used in this script but may be added for HL7 validation):
# - hl7apy: For HL7 message parsing and validation
#   Install with: pip install hl7apy
# To install all required dependencies, run:
#   pip install pandas
# If adding hl7apy later, run:
#   pip install hl7apy pandas

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import pandas as pd
import random
import os
import re
from datetime import datetime, timedelta

# Define color scheme
BG_COLOR = "#1F2139"  # Dark blue-gray background
TEXT_COLOR = "#FFFFFF"  # White text
PREVIEW_BG = "#1E1E1E"  # Near-black for preview areas
TITLE_HL7_MSG = "#465BE7"  # Blue for "HL7 Message" title
TITLE_CREATOR = "#7DCAE3"  # Light blue for "Creator & Editor" title
TITLE_EDITOR = "#7DCAE3"  # Light blue for Editor
DITHERED_TEXT = "#808080"  # Gray for disabled elements

# Directory for CSVs and output (same as script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR  # CSVs and folders are in the same directory as the script

# Default HL7 template
default_hl7 = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||SIU^S12|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|S|^^^{YYYYMMDD}{scheduledTime}
ZCS||Y|ORSCH_S14||||{cptCode}^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||{patientDOB}|{patientGender}|{patientLastName}^{patientFirstName}^^|||||||||{patientMRN}
PV1||IP|NC-PERIOP^^^NC|||||||GEN|||||||||{patientMRN}
RGS|
OBX|1|DTM|{caseEvent}|In|{YYYYMMDD}{eventTime}|||||||||{YYYYMMDD}{eventTime}||||||||||||||||||
AIS|1||{procedureId}^{procedure}|{YYYYMMDD}{scheduledTime}|0|S|4500|S||||2
NTE|1||{procedureDescription}|Procedure Description|||
NTE|2||{specialNeeds}|Case Notes|||
AIL|1||^{locationOR}^^{locationDepartment}
AIP|1||9941778^{primaryLastName}^{primaryFirstName}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|2||99225747^{lastName}^{firstName}^E^^^^^EPIC^^^^PROVID|4.20^Circulator||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|3||99252693^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|4.150^Scrub||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|4||99252694^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|5||99252695^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
"""

# Case events
case_events = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -45),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", "duration-30"),
    ("complete", "duration-15"),
    ("exiting", "duration-10"),
    ("ordered_pacu", "exiting-5"),
    ("planned_pacu", "exiting-5"),
    ("in_pacu", "exiting+5"),
    ("out_pacu", "in_pacu+60"),
]

# Default font settings
DEFAULT_FONT = ("Arial", 10)  # Changed from 12 to 10

# Custom UppercaseEntry widget
class UppercaseEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        tk.Entry.__init__(self, *args, **kwargs, font=DEFAULT_FONT)
        self.bind("<KeyRelease>", self.to_upper)

    def to_upper(self, event):
        current_text = self.get()
        self.delete(0, tk.END)
        self.insert(0, current_text.upper())

# Main application class
class HL7MessageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HL7 Message Creator")  # Initial title
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("1185x1160")  # Set default window size to 1185x1160
        self.root.minsize(800, 600)  # Retain minimum size

        # Set dark theme for ttk widgets
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TFrame", background=BG_COLOR)
            style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=DEFAULT_FONT)
            style.configure("TButton", background=BG_COLOR, foreground=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT)
            style.configure("Treeview", background=PREVIEW_BG, foreground=TEXT_COLOR, fieldbackground=PREVIEW_BG, font=DEFAULT_FONT)
            style.map("Treeview", background=[("selected", "#3A3C5A")])
            style.configure("Vertical.TScrollbar", background=BG_COLOR, troughcolor=BG_COLOR, arrowcolor=TEXT_COLOR)
            style.map("Vertical.TScrollbar",
                      background=[("active", "#3A3C5A")],
                      arrowcolor=[("active", TEXT_COLOR)])
        except tk.TclError as e:
            print(f"Theme setup warning: {e}")

        # Load CSVs
        try:
            self.procedures = pd.read_csv(os.path.join(DATA_DIR, "procedures.csv"), delimiter=',')
            self.staff_names = pd.read_csv(os.path.join(DATA_DIR, "staff_names.csv"), delimiter=',')
            self.surgeon_names = pd.read_csv(os.path.join(DATA_DIR, "surgeon_names.csv"), delimiter=',')
            self.patient_names = pd.read_csv(os.path.join(DATA_DIR, "patient_names.csv"), delimiter=',')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV files: {str(e)}")
            self.root.quit()
            return

        # Initialize state variables
        self.patients = []
        self.current_patient_index = -1
        self.procedure_panel_visible = False
        self.procedure_frames = []
        self.folders = ["CurrentDay", "NextDay", "PreviousDay"]
        self.current_block = -1
        self.patient_blocks = []
        self.edited_messages = {}
        self.manual_entries = {}
        self.edit_fields = []

        # Create menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        file_menu.add_command(label="Quit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        view_menu.add_command(label="Creator", command=lambda: self.set_mode("Creator"))
        view_menu.add_command(label="Editor", command=lambda: self.set_mode("Editor"))
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        help_menu.add_command(label="Help", command=self.open_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Content frame
        self.content_frame = tk.Frame(root, bg=BG_COLOR)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Start with Creator mode
        self.set_mode("Creator")

    def set_mode(self, mode):
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        if mode == "Creator":
            self.root.title("HL7 Message Creator")
            self.setup_creator()
        elif mode == "Editor":
            self.root.title("HL7 Message Editor")
            self.setup_editor()

    def open_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - User Manual")
        help_window.configure(bg=BG_COLOR)

        help_text = scrolledtext.ScrolledText(
            help_window, width=80, height=30, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT
        )
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        help_content = """
        HL7 Message Creator and Editor - User Manual

        Welcome to the HL7 Message Creator and Editor!

        This application allows you to create and edit HL7 messages for testing purposes.

        **Creator Mode**
        - Use "Create New Patient" to start creating HL7 messages.
        - Fill in patient details, procedure info, and staff members.
        - Use "Random" buttons to populate fields with random CSV data.
        - Click "Create" to generate HL7 messages.
        - Use "Save & Exit" to save messages to the output folder.

        **Editor Mode**
        - Loads HL7 messages from CurrentDay, NextDay, or PreviousDay folders.
        - Navigate patient blocks with "Previous" and "Next".
        - Edit messages manually or use "Randomize All" for names.
        - Save changes with "Save and Exit".

        For more details, contact the developer.
        """
        help_text.insert(tk.END, help_content)
        help_text.config(state="disabled")

    def show_about(self):
        about_text = """HL7 Message Creator
Version: 1.0
Description: This application is designed to create and edit HL7 messages for testing purposes.
Author: J.M.Thomas"""
        messagebox.showinfo("About", about_text)

    # --- Creator Mode ---
    def setup_creator(self):
        # Main container
        self.creator_main_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.creator_main_container.pack(fill=tk.BOTH, expand=True)

        # Procedure browser panel
        self.procedure_frame = tk.Frame(self.creator_main_container, bg=BG_COLOR, width=350)
        self.procedure_frame.pack_propagate(False)
        self.setup_procedure_browser()

        # Right-side content frame with scrolling (no visible scrollbar)
        self.creator_content_container = tk.Frame(self.creator_main_container, bg=BG_COLOR)
        self.creator_content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a canvas for scrolling (without a visible scrollbar)
        self.canvas = tk.Canvas(self.creator_content_container, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a frame inside the canvas to hold all content
        self.creator_content_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.creator_content_frame, anchor="nw")

        # Bind canvas resizing
        self.creator_content_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        # Preview text box
        self.creator_preview_text = scrolledtext.ScrolledText(
            self.creator_content_frame, width=160, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT
        )
        self.creator_preview_text.pack(fill=tk.X, pady=(0, 10))

        # Top button frame (Previous, Next, Browse Procedures, Create New Patient, Quit, Save & Exit)
        self.creator_button_container_top = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.creator_button_container_top.pack(fill=tk.X)
        self.creator_button_frame_top = tk.Frame(self.creator_button_container_top, bg=BG_COLOR)
        self.creator_button_frame_top.pack(pady=5)

        # Navigation buttons
        self.creator_prev_button = tk.Button(
            self.creator_button_frame_top, text="Previous", command=self.creator_prev_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        )
        self.creator_prev_button.pack(side=tk.LEFT, padx=5)
        self.creator_next_button = tk.Button(
            self.creator_button_frame_top, text="Next", command=self.creator_next_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        )
        self.creator_next_button.pack(side=tk.LEFT, padx=5)

        # Command buttons
        tk.Button(
            self.creator_button_frame_top, text="Browse Procedures", command=self.toggle_procedure_browser, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_top, text="Create New Patient", command=self.create_new_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_top, text="Quit", command=self.quit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_top, text="Save & Exit", command=self.creator_save_and_exit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)

        # Base prompts frame
        self.base_prompts_frame = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.base_prompts_frame.pack(fill=tk.X, pady=5)
        self.base_entries = {}
        self.staff_entries = {}
        self.additional_staff = []
        self.setup_base_prompts()

        # Procedures frame
        self.procedures_frame = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.procedures_frame.pack(fill=tk.X, pady=5)

        # Bottom button frame (Add Procedure, Remove Last Procedure, Add Staff Member, Random Patient, Random Surgeon, Random Staff)
        self.creator_button_container_bottom = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.creator_button_container_bottom.pack(fill=tk.X)
        self.creator_button_frame_bottom = tk.Frame(self.creator_button_container_bottom, bg=BG_COLOR)
        self.creator_button_frame_bottom.pack(pady=5)

        tk.Button(
            self.creator_button_frame_bottom, text="Add Procedure", command=self.add_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_bottom, text="Remove Last Procedure", command=self.remove_last_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_bottom, text="Add Staff Member", command=self.add_staff_member, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_bottom, text="Random Patient", command=self.random_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_bottom, text="Random Surgeon", command=self.random_surgeon, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.creator_button_frame_bottom, text="Random Staff", command=self.random_staff, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)

        # Create button (remains centered below)
        self.create_button = tk.Button(
            self.creator_content_frame, text="Create", command=self.create_patient, bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 14), activebackground="#3A3C5A"  # Changed from 16 to 14
        )
        self.create_button.pack(pady=10)

        # Update button states and load patient if exists
        self.creator_update_button_states()
        if self.patients and 0 <= self.current_patient_index < len(self.patients):
            self.creator_load_patient()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_procedure_browser(self):
        search_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_procedures())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Treeview control buttons
        tree_control_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        tree_control_frame.pack(fill=tk.X, pady=5)
        tree_control_inner = tk.Frame(tree_control_frame, bg=BG_COLOR)
        tree_control_inner.pack()
        tk.Button(
            tree_control_inner, text="Collapse All", command=self.collapse_all_procedures, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            tree_control_inner, text="Expand All", command=self.expand_all_procedures, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.procedure_frame, show="tree", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.select_procedure)

        button_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(
            button_frame, text="Choose Random", command=self.choose_random_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            button_frame, text="Close", command=self.toggle_procedure_browser, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)

        self.populate_procedure_tree()

    def collapse_all_procedures(self):
        for item in self.tree.get_children():
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                self.tree.item(child, open=False)

    def expand_all_procedures(self):
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                self.tree.item(child, open=True)

    def populate_procedure_tree(self, filter_text=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        filter_text = filter_text.lower()
        specialties = self.procedures["specialty"].unique()
        for spec in specialties:
            spec_has_match = False
            spec_id = None
            categories = self.procedures[self.procedures["specialty"] == spec]["category"].unique()
            for cat in categories:
                cat_has_match = False
                cat_id = None
                procs = self.procedures[(self.procedures["specialty"] == spec) & (self.procedures["category"] == cat)]
                for _, proc in procs.iterrows():
                    proc_text = f"{proc['name']} (CPT: {proc['cpt']})"
                    # Convert cpt and id to strings to handle numeric values
                    cpt_str = str(proc["cpt"]).lower()
                    id_str = str(proc["id"]).lower()
                    if not filter_text or (
                        filter_text in spec.lower() or
                        filter_text in cat.lower() or
                        filter_text in proc_text.lower() or
                        filter_text in id_str or
                        filter_text in cpt_str
                    ):
                        if not spec_has_match:
                            spec_id = self.tree.insert("", tk.END, text=spec)
                            spec_has_match = True
                        if not cat_has_match:
                            cat_id = self.tree.insert(spec_id, tk.END, text=cat)
                            cat_has_match = True
                        self.tree.insert(cat_id, tk.END, text=proc_text, values=(proc["name"], proc["id"], proc["description"], proc["special_needs"], proc["cpt"]))

    def filter_procedures(self):
        filter_text = self.search_var.get()
        self.populate_procedure_tree(filter_text)

    def apply_procedure_selection(self, proc_name, proc_id, proc_desc, proc_needs, proc_cpt):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if not patient["base_vars"]["{procedure}"].get() and not patient["procedures"]:
                patient["base_vars"]["{procedure}"].set(proc_name)
                patient["base_vars"]["{procedureId}"].set(proc_id)
                patient["base_vars"]["{procedureDescription}"].set(proc_desc)
                patient["base_vars"]["{specialNeeds}"].set(proc_needs)
                patient["base_vars"]["{cptCode}"].set(proc_cpt)
            else:
                if patient["procedures"]:
                    proc = patient["procedures"][-1]
                    proc["{procedure}"].set(proc_name)
                    proc["{procedureId}"].set(proc_id)
                    proc["{procedureDescription}"].set(proc_desc)
                    proc["{specialNeeds}"].set(proc_needs)
                    proc["{locationDepartment}"].set("{locationDepartment}")
                    proc["{locationOR}"].set("{locationOR}")
                else:
                    new_proc = {
                        "{procedure}": tk.StringVar(value=proc_name),
                        "{procedureId}": tk.StringVar(value=proc_id),
                        "{procedureDescription}": tk.StringVar(value=proc_desc),
                        "{specialNeeds}": tk.StringVar(value=proc_needs),
                        "{locationDepartment}": tk.StringVar(value="{locationDepartment}"),
                        "{locationOR}": tk.StringVar(value="{locationOR}")
                    }
                    patient["procedures"].append(new_proc)
                    self.add_procedure_fields(new_proc)
            self.creator_update_preview()

    def select_procedure(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            values = item.get("values")
            if values and len(values) == 5:
                proc_name, proc_id, proc_desc, proc_needs, proc_cpt = values
                self.apply_procedure_selection(proc_name, proc_id, proc_desc, proc_needs, proc_cpt)

    def choose_random_procedure(self):
        if 0 <= self.current_patient_index < len(self.patients):
            proc = self.procedures.sample(1).iloc[0]
            self.apply_procedure_selection(
                proc["name"], proc["id"], proc["description"], proc["special_needs"], proc["cpt"]
            )

    def toggle_procedure_browser(self):
        if self.procedure_panel_visible:
            self.procedure_frame.pack_forget()
            self.procedure_panel_visible = False
        else:
            self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            self.procedure_panel_visible = True

    def setup_base_prompts(self):
        for prompt in base_prompts:
            frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.base_entries[prompt['key']] = entry

        self.staff_group_frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
        self.staff_group_frame.pack(fill=tk.X, pady=10)

        self.fixed_roles = [
            {"role": "Primary Surgeon", "code": "1.1^Primary", "id": "9941778", "last_key": "{primaryLastName}", "first_key": "{primaryFirstName}"},
            {"role": "Circulator", "code": "4.20^Circulator", "id": "99225747", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Scrub", "code": "4.150^Scrub", "id": "99252693", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "CRNA", "code": "2.20^ANE CRNA", "id": "99252694", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Anesthesiologist", "code": "2.139^Anesthesiologist", "id": "99252695", "last_key": "{lastName}", "first_key": "{firstName}"},
        ]

        for i, role_info in enumerate(self.fixed_roles):
            role = role_info["role"]
            row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
            row_frame.grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(row_frame, text=f"{role}:", fg=TEXT_COLOR, bg=BG_COLOR, width=15, anchor="w", font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, width=5, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            last_entry = UppercaseEntry(row_frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
            last_entry.pack(side=tk.LEFT, padx=2)
            tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, width=5, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            first_entry = UppercaseEntry(row_frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
            first_entry.pack(side=tk.LEFT, padx=2)
            last_var = tk.StringVar()
            first_var = tk.StringVar()
            last_entry.config(textvariable=last_var)
            first_entry.config(textvariable=first_var)
            last_var.trace_add("write", lambda *args: self.creator_update_preview())
            first_var.trace_add("write", lambda *args: self.creator_update_preview())
            self.staff_entries[role] = {"lastName": last_var, "firstName": first_var}

    def random_patient(self):
        name = self.patient_names.sample(1).iloc[0]
        self.base_entries["{patientFirstName}"].config(textvariable=tk.StringVar(value=name["First Name"]))
        self.base_entries["{patientLastName}"].config(textvariable=tk.StringVar(value=name["Last Name"]))
        self.creator_update_preview()

    def random_surgeon(self):
        name = self.surgeon_names.sample(1).iloc[0]
        self.staff_entries["Primary Surgeon"]["firstName"].set(name["First Name"])
        self.staff_entries["Primary Surgeon"]["lastName"].set(name["Last Name"])
        self.creator_update_preview()

    def random_staff(self):
        for role in self.staff_entries:
            if role != "Primary Surgeon":
                name = self.staff_names.sample(1).iloc[0]
                self.staff_entries[role]["firstName"].set(name["First Name"])
                self.staff_entries[role]["lastName"].set(name["Last Name"])
        for staff in self.additional_staff:
            name = self.staff_names.sample(1).iloc[0]
            staff["vars"]["firstName"].set(name["First Name"])
            staff["vars"]["lastName"].set(name["Last Name"])
        self.creator_update_preview()

    def creator_update_button_states(self):
        if len(self.patients) <= 1:
            self.creator_prev_button.config(state="disabled", fg=DITHERED_TEXT)
            self.creator_next_button.config(state="disabled", fg=DITHERED_TEXT)
        elif self.current_patient_index <= 0:
            self.creator_prev_button.config(state="disabled", fg=DITHERED_TEXT)
            self.creator_next_button.config(state="normal", fg=TEXT_COLOR)
        elif self.current_patient_index >= len(self.patients) - 1:
            self.creator_prev_button.config(state="normal", fg=TEXT_COLOR)
            self.creator_next_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.creator_prev_button.config(state="normal", fg=TEXT_COLOR)
            self.creator_next_button.config(state="normal", fg=TEXT_COLOR)

    def create_new_patient(self):
        patient = {
            'base_vars': {prompt['key']: tk.StringVar(value='') for prompt in base_prompts},
            'procedures': [],
            'staff_members': [],
            'messages': []
        }
        self.patients.append(patient)
        self.current_patient_index = len(self.patients) - 1
        self.creator_load_patient()

    def creator_load_patient(self):
        patient = self.patients[self.current_patient_index]
        for key, entry in self.base_entries.items():
            var = patient['base_vars'][key]
            entry.config(textvariable=var)
            var.trace_remove("write", var.trace_info()[0][1]) if var.trace_info() else None
            var.trace_add("write", lambda *args: self.creator_update_preview())
        for role in self.staff_entries:
            self.staff_entries[role]["lastName"].set("")
            self.staff_entries[role]["firstName"].set("")
        for staff in patient['staff_members']:
            self.add_staff_fields(staff)
        for widget in self.procedures_frame.winfo_children():
            widget.destroy()
        self.procedure_frames = []
        for proc in patient['procedures']:
            self.add_procedure_fields(proc)
        self.creator_update_preview()
        self.creator_update_button_states()

    def add_procedure(self):
        proc = {
            "{procedure}": tk.StringVar(value="{procedure}"),
            "{procedureDescription}": tk.StringVar(value="{procedureDescription}"),
            "{specialNeeds}": tk.StringVar(value="{specialNeeds}"),
            "{locationDepartment}": tk.StringVar(value="{locationDepartment}"),
            "{locationOR}": tk.StringVar(value="{locationOR}"),
            "{procedureId}": tk.StringVar(value="{procedureId}")
        }
        self.patients[self.current_patient_index]['procedures'].append(proc)
        self.add_procedure_fields(proc)
        self.creator_update_preview()

    def remove_last_procedure(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if patient['procedures']:  # If additional procedures exist
                patient['procedures'].pop()  # Remove the last procedure
                # Remove the last procedure frame from the GUI
                if self.procedure_frames:
                    self.procedure_frames[-1].destroy()
                    self.procedure_frames.pop()
            else:  # Only the base procedure exists
                # Reset base procedure fields to template defaults
                patient['base_vars']['{procedure}'].set("{procedure}")
                patient['base_vars']['{procedureDescription}'].set("{procedureDescription}")
                patient['base_vars']['{specialNeeds}'].set("{specialNeeds}")
                patient['base_vars']['{procedureId}'].set("{procedureId}")
                patient['base_vars']['{cptCode}'].set("{cptCode}")
            self.creator_update_preview()

    def add_procedure_fields(self, proc):
        frame = tk.Frame(self.procedures_frame, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=5)
        self.procedure_frames.append(frame)
        for field in procedure_fields:
            subframe = tk.Frame(frame, bg=BG_COLOR)
            subframe.pack(fill=tk.X, pady=2)
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, textvariable=proc[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            proc[field['key']].trace_add("write", lambda *args: self.creator_update_preview())

    def add_staff_member(self):
        staff = {
            "role": tk.StringVar(value="Staff"),
            "lastName": tk.StringVar(value=""),
            "firstName": tk.StringVar(value="")
        }
        self.patients[self.current_patient_index]['staff_members'].append(staff)
        self.add_staff_fields(staff)

    def add_staff_fields(self, staff):
        row = len(self.staff_entries) + len(self.additional_staff)
        row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
        row_frame.grid(row=row, column=0, sticky="w", pady=2)
        role_entry = UppercaseEntry(row_frame, textvariable=staff["role"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=15)
        role_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row_frame, text=":", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, width=5, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        last_entry = UppercaseEntry(row_frame, textvariable=staff["lastName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
        last_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, width=5, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        first_entry = UppercaseEntry(row_frame, textvariable=staff["firstName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
        first_entry.pack(side=tk.LEFT, padx=2)
        staff["role"].trace_add("write", lambda *args: self.creator_update_preview())
        staff["lastName"].trace_add("write", lambda *args: self.creator_update_preview())
        staff["firstName"].trace_add("write", lambda *args: self.creator_update_preview())
        self.additional_staff.append({"frame": row_frame, "vars": staff})

    def creator_update_preview(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            template = self.add_staff_segment(template)
            s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
            base_values = {k: v.get() for k, v in patient['base_vars'].items() if v.get()}
            preview_text = s12_template
            for key, val in base_values.items():
                preview_text = preview_text.replace(key, val)
            self.creator_preview_text.delete(1.0, tk.END)
            self.creator_preview_text.insert(tk.END, preview_text)

    def build_template(self, patient):
        template = default_hl7
        procedures = patient['procedures']
        for i, proc in enumerate(procedures, start=2):
            proc_values = {k: v.get() for k, v in proc.items() if v.get()}
            template = self.add_procedure_segments(template, i, proc_values)
        return template

    def add_procedure_segments(self, template, proc_num, proc_values):
        lines = template.splitlines()
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("AIS|1|"))
        end_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|1|")) + 1
        proc_block = lines[start_idx:end_idx]
        new_block = []
        nte_count = 2 * (proc_num - 1)
        for line in proc_block:
            if line.startswith("AIS|1|"):
                new_line = line.replace("AIS|1|", f"AIS|{proc_num}|")
            elif line.startswith("NTE|1|"):
                nte_count += 1
                new_line = line.replace("NTE|1|", f"NTE|{nte_count}|")
            elif line.startswith("NTE|2|"):
                nte_count += 1
                new_line = line.replace("NTE|2|", f"NTE|{nte_count}|")
            elif line.startswith("AIL|1|"):
                new_line = line.replace("AIL|1|", f"AIL|{proc_num}|")
            else:
                new_line = line
            for key, val in proc_values.items():
                new_line = new_line.replace(key, val)
            new_block.append(new_line)
        insert_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|")) + 1
        lines[insert_idx:insert_idx] = new_block
        return "\n".join(lines)

    def add_staff_segment(self, template):
        lines = template.splitlines()
        lines = [line for line in lines if not line.startswith("AIP|")]
        insert_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|")) + 1
        new_aip_lines = []
        for i, role_info in enumerate(self.fixed_roles, start=1):
            role = role_info["role"]
            code = role_info["code"]
            provider_id = role_info["id"]
            last_key = role_info["last_key"]
            first_key = role_info["first_key"]
            last_name = self.staff_entries[role]["lastName"].get()
            first_name = self.staff_entries[role]["firstName"].get()
            last_name = last_name if last_name else last_key
            first_name = first_name if first_name else first_key
            aip_line = f"AIP|{i}||{provider_id}^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|{code}|GEN|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)
        aip_count = len(self.fixed_roles)
        for staff in self.patients[self.current_patient_index]['staff_members']:
            aip_count += 1
            role = staff["role"].get() or "Staff"
            last_name = staff["lastName"].get()
            first_name = staff["firstName"].get()
            last_name = last_name if last_name else "{lastName}"
            first_name = first_name if first_name else "{firstName}"
            aip_line = f"AIP|{aip_count}||99252695^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)
        lines[insert_idx:insert_idx] = new_aip_lines
        return "\n".join(lines)

    def get_event_time(self, base_time, offset, duration, event_times):
        if isinstance(offset, str):
            if offset.startswith("duration"):
                delta = int(offset.split("-")[1])
                minutes = duration - delta
            elif offset.startswith("exiting"):
                exiting_time = event_times["exiting"]
                delta = int(offset.split("exiting")[1])
                return exiting_time + timedelta(minutes=delta + random.randint(-2, 2))
            elif offset.startswith("in_pacu"):
                in_pacu_time = event_times["in_pacu"]
                delta = int(offset.split("+")[1])
                return in_pacu_time + timedelta(minutes=delta + random.randint(-2, 2))
            else:
                minutes = int(offset)
        else:
            minutes = offset
        return base_time + timedelta(minutes=minutes + random.randint(-2, 2))

    def fill_template(self, template, replacements):
        for key, val in replacements.items():
            template = template.replace(key, val)
        return template

    def build_event_messages(self, template, base_values, duration_min):
        base_date = base_values.get("{YYYYMMDD}", "{YYYYMMDD}")
        setup_time = base_values.get("{scheduledTime}", "{scheduledTime}")
        if base_date == "{YYYYMMDD}" or setup_time == "{scheduledTime}" or not base_date or not setup_time:
            messages = [(template, "00")]
            for i, (event_name, _) in enumerate(case_events):
                event_replacements = base_values.copy()
                event_replacements["{caseEvent}"] = event_name
                event_msg = self.fill_template(template, event_replacements)
                messages.append((event_msg, f"{i+1:02}"))
            return messages
        setup_time_clean = setup_time.replace(":", "")
        try:
            datetime.strptime(f"{base_date} {setup_time_clean}", "%Y%m%d %H%M%S")
        except ValueError:
            messages = [(template, "00")]
            for i, (event_name, _) in enumerate(case_events):
                event_replacements = base_values.copy()
                event_replacements["{caseEvent}"] = event_name
                event_msg = self.fill_template(template, event_replacements)
                messages.append((event_msg, f"{i+1:02}"))
            return messages
        setup_dt = datetime.strptime(f"{base_date} {setup_time_clean}", "%Y%m%d %H%M%S")
        messages = []
        event_times = {}
        s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
        s12_time = setup_dt.strftime("%H%M%S")
        s12_replacements = base_values.copy()
        s12_replacements["{eventTime}"] = s12_time
        s12_msg = self.fill_template(s12_template, s12_replacements)
        messages.append((s12_msg, "00"))
        for event_name, offset in case_events:
            event_time = self.get_event_time(setup_dt, offset, duration_min, event_times)
            event_times[event_name] = event_time
        for i, (event_name, _) in enumerate(case_events):
            event_time = event_times[event_name]
            time_str = event_time.strftime("%H%M%S")
            date_str = event_time.strftime("%Y%m%d")
            event_replacements = base_values.copy()
            event_replacements["{eventTime}"] = time_str
            event_replacements["{caseEvent}"] = event_name
            event_replacements["{YYYYMMDD}"] = date_str
            event_msg = self.fill_template(template, event_replacements)
            messages.append((event_msg, f"{i+1:02}"))
        return messages

    def create_patient(self):
        patient = self.patients[self.current_patient_index]
        template = self.build_template(patient)
        template = self.add_staff_segment(template)
        base_values = {k: v.get() for k, v in patient['base_vars'].items()}
        duration_str = base_values.get("{duration}", "")
        duration_min = int(duration_str) if duration_str.isdigit() else random.randint(60, 120)
        messages = self.build_event_messages(template, base_values, duration_min)
        patient['messages'] = messages
        messagebox.showinfo("Patient Created", "Patient messages generated. You can still edit the fields.")

    def creator_prev_patient(self):
        if self.current_patient_index > 0:
            self.current_patient_index -= 1
            self.creator_load_patient()

    def creator_next_patient(self):
        if self.current_patient_index < len(self.patients) - 1:
            self.current_patient_index += 1
            self.creator_load_patient()

    def creator_save_and_exit(self):
        out_dir = os.path.join(DATA_DIR, f"{datetime.now():%y%m%d}-HL7 Output")
        os.makedirs(out_dir, exist_ok=True)
        total_messages = 0
        total_patients = 0
        for patient in self.patients:
            if 'messages' in patient and patient['messages']:
                total_patients += 1
                total_messages += len(patient['messages'])
                base_name = f"{patient['base_vars']['{patientFirstName}'].get() or 'First'}{patient['base_vars']['{patientLastName}'].get() or 'Last'}"
                for msg, idx in patient['messages']:
                    filename = f"{base_name}-{idx}.hl7"
                    with open(os.path.join(out_dir, filename), 'w') as f:
                        f.write(msg)
        messagebox.showinfo(
            "Save Complete",
            f"{total_messages} messages for {total_patients} patients have been created and saved to {out_dir}"
        )
        self.root.quit()

    # --- Editor Mode ---
    def setup_editor(self):
        self.editor_content_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.editor_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.editor_preview_text = scrolledtext.ScrolledText(
            self.editor_content_frame, width=80, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT
        )
        self.editor_preview_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.editor_button_container = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.editor_button_container.pack(fill=tk.X)
        self.editor_button_frame = tk.Frame(self.editor_button_container, bg=BG_COLOR)
        self.editor_button_frame.pack(pady=5)

        self.editor_prev_button = tk.Button(
            self.editor_button_frame, text="Previous", command=self.editor_prev_block, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        )
        self.editor_prev_button.pack(side=tk.LEFT, padx=5)
        self.editor_next_button = tk.Button(
            self.editor_button_frame, text="Next", command=self.editor_next_block, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        )
        self.editor_next_button.pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.editor_button_frame, text="Randomize All", command=self.editor_randomize_all, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.editor_button_frame, text="Quit", command=self.quit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.editor_button_frame, text="Save and Exit", command=self.editor_save_and_exit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
        ).pack(side=tk.LEFT, padx=5)

        self.editor_prompt_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.editor_prompt_frame.pack(fill=tk.X, pady=5)

        self.editor_edit_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.editor_edit_frame.pack(fill=tk.X, pady=5, anchor='w')

        self.editor_load_blocks()
        self.editor_next_block()

    def editor_load_blocks(self):
        self.patient_blocks = self.get_patient_blocks(self.folders)
        if not self.patient_blocks:
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, "No HL7 files found in CurrentDay, NextDay, or PreviousDay.\n")

    def get_patient_blocks(self, folders):
        patient_blocks = []
        for folder in folders:
            folder_path = os.path.join(DATA_DIR, folder)
            if not os.path.exists(folder_path):
                continue
            files = [f for f in os.listdir(folder_path) if f.endswith(".hl7")]
            patient_groups = {}
            for file in files:
                patient_name = file.split('-')[0] if '-' in file else file.replace(".hl7", "")
                if patient_name not in patient_groups:
                    patient_groups[patient_name] = []
                patient_groups[patient_name].append(os.path.join(folder_path, file))
            for patient_name, patient_files in patient_groups.items():
                patient_files.sort()
                patient_blocks.append((folder, patient_name, patient_files))
        return sorted(patient_blocks, key=lambda x: (x[0], x[1]))

    def replace_variables(self, message, primary_fname, primary_lname, staff_names, manual_values=None):
        if manual_values:
            temp_message = message
            for (var, instance), value in manual_values.items():
                if instance:
                    lines = temp_message.split('\n')
                    for i, line in enumerate(lines):
                        if instance in line and var in line:
                            lines[i] = lines[i].replace(var, value, 1)
                    temp_message = '\n'.join(lines)
                else:
                    temp_message = temp_message.replace(var, value)
            return temp_message
        message = message.replace("{primaryFirstName}", primary_fname)
        message = message.replace("{primaryLastName}", primary_lname)
        def replace_staff(match):
            var = match.group(1)
            if var == "firstName":
                return random.choice(staff_names[["First Name"]].values)[0]
            elif var == "lastName":
                return random.choice(staff_names[["Last Name"]].values)[0]
            return match.group(0)
        return re.sub(r"\{(firstName|lastName)\}", replace_staff, message)

    def find_variable_instances(self, message):
        instances = []
        lines = message.split('\n')
        for line in lines:
            if '{primaryLastName}' in line or '{primaryFirstName}' in line:
                if line.startswith('PV1'):
                    if '{primaryLastName}' in line:
                        instances.append(('PV1', '{primaryLastName}'))
                    if '{primaryFirstName}' in line:
                        instances.append(('PV1', '{primaryFirstName}'))
                elif line.startswith('AIP'):
                    seq = line.split('|')[1]
                    if '{primaryLastName}' in line:
                        instances.append((f'AIP|{seq}', '{primaryLastName}'))
                    if '{primaryFirstName}' in line:
                        instances.append((f'AIP|{seq}', '{primaryFirstName}'))
            if '{lastName}' in line or '{firstName}' in line:
                if line.startswith('AIP'):
                    seq = line.split('|')[1]
                    if '{lastName}' in line:
                        instances.append((f'AIP|{seq}', '{lastName}'))
                    if '{firstName}' in line:
                        instances.append((f'AIP|{seq}', '{firstName}'))
        return sorted(set(instances), key=lambda x: x[0])

    def editor_update_button_states(self):
        if self.current_block <= 0:
            self.editor_prev_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.editor_prev_button.config(state="normal", fg=TEXT_COLOR)
        if self.current_block >= len(self.patient_blocks) - 1:
            self.editor_next_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.editor_next_button.config(state="normal", fg=TEXT_COLOR)

    def editor_show_prompt(self, message, options, callback):
        for widget in self.editor_prompt_frame.winfo_children():
            widget.destroy()
        tk.Label(self.editor_prompt_frame, text=message, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        for option in options:
            tk.Button(
                self.editor_prompt_frame, text=option, command=lambda o=option: callback(o),
                bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
            ).pack(side=tk.LEFT, padx=5)

    def editor_clear_edit_fields(self):
        for widget in self.editor_edit_frame.winfo_children():
            widget.destroy()
        self.edit_fields = []
        self.manual_entries = {}

    def editor_highlight_variable(self, instance, var, message):
        self.editor_preview_text.tag_remove("highlight", "1.0", tk.END)
        if not message:
            return
        lines = message.split('\n')
        for line in lines:
            if instance in line and var in line:
                start_idx = line.find(var)
                if start_idx != -1:
                    line_num = lines.index(line) + 1
                    start_pos = f"{line_num}.{start_idx}"
                    end_pos = f"{line_num}.{start_idx + len(var)}"
                    self.editor_preview_text.tag_add("highlight", start_pos, end_pos)
                    self.editor_preview_text.tag_config("highlight", background="yellow", foreground="black")
                    break

    def editor_update_preview(self):
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            with open(block_files[0], 'r') as file:
                message = file.read()
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, message)
            self.editor_show_prompt(f"Edit patient block ({patient})?", ["Yes", "No"], self.editor_handle_edit_prompt)
        else:
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, "No more patient blocks.\n")
            for widget in self.editor_prompt_frame.winfo_children():
                widget.destroy()
        self.editor_update_button_states()

    def editor_handle_edit_prompt(self, choice):
        if choice == "Yes":
            self.editor_show_prompt("Randomize or manually edit?", ["Random", "Manual"], self.editor_handle_mode_choice)
        else:
            self.editor_next_block()

    def editor_handle_mode_choice(self, choice):
        if choice == "Random":
            self.editor_randomize_block()
        else:
            self.editor_manual_edit_block()

    def editor_prev_block(self):
        if self.current_block > 0:
            self.current_block -= 1
            self.editor_clear_edit_fields()
            self.editor_update_preview()

    def editor_next_block(self):
        if self.current_block < len(self.patient_blocks) - 1:
            self.current_block += 1
            self.editor_clear_edit_fields()
            self.editor_update_preview()

    def editor_randomize_all(self):
        self.editor_show_prompt("This will randomize all names for all messages. Proceed?", ["Yes", "No"], self.editor_handle_randomize_all)

    def editor_handle_randomize_all(self, choice):
        if choice == "Yes":
            self.edited_messages = {}
            total_messages = 0
            total_patients = len(self.patient_blocks)
            for folder, patient, block_files in self.patient_blocks:
                primary = self.surgeon_names.sample(1).iloc[0]
                primary_fname, primary_lname = primary["First Name"], primary["Last Name"]
                for file_path in block_files:
                    with open(file_path, 'r') as file:
                        message = file.read()
                    self.edited_messages[file_path] = self.replace_variables(message, primary_fname, primary_lname, self.staff_names)
                    total_messages += 1
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, "Randomization complete.\n")
            self.editor_show_prompt(f"{total_messages} messages for {total_patients} patients were edited.", ["OK"], lambda x: self.editor_update_preview())
        else:
            self.editor_update_preview()

    def editor_randomize_block(self):
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            primary = self.surgeon_names.sample(1).iloc[0]
            primary_fname, primary_lname = primary["First Name"], primary["Last Name"]
            edited = {}
            for file_path in block_files:
                with open(file_path, 'r') as file:
                    message = file.read()
                edited[file_path] = self.replace_variables(message, primary_fname, primary_lname, self.staff_names)
            self.edited_messages.update(edited)
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, edited[block_files[0]])
            self.editor_show_prompt("Save and proceed, reroll, or edit manually?", ["Save", "Reroll", "Manual"], self.editor_handle_post_edit)

    def editor_manual_edit_block(self):
        if 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            with open(block_files[0], 'r') as file:
                message = file.read()
            instances = self.find_variable_instances(message)
            self.editor_clear_edit_fields()
            for instance, var in instances:
                frame = tk.Frame(self.editor_edit_frame, bg=PREVIEW_BG)
                frame.pack(fill=tk.X, pady=2, anchor='w')
                tk.Label(frame, text=f"{instance}", fg=TEXT_COLOR, bg=PREVIEW_BG, width=10, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
                entry = tk.Entry(frame, bg=PREVIEW_BG, fg=DITHERED_TEXT, insertbackground=TEXT_COLOR, font=DEFAULT_FONT)
                entry.insert(0, var)
                entry.bind("<FocusIn>", lambda e, i=instance, v=var: self.editor_on_entry_focus(e, i, v, entry))
                entry.bind("<KeyRelease>", lambda e, i=instance, v=var, fp=block_files[0]: self.editor_on_entry_change(e, i, v, entry, fp))
                entry.pack(side=tk.LEFT, padx=5)
                self.edit_fields.append((entry, instance, var))
            random_patient_button = tk.Button(
                self.editor_edit_frame, text="Random Patient", command=self.editor_random_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A", font=DEFAULT_FONT
            )
            random_patient_button.pack(pady=5)
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, message)
            self.editor_show_prompt("Apply manual edits?", ["Apply", "Cancel"], self.editor_handle_manual_apply)

    def editor_random_patient(self):
        if 0 <= self.current_block < len(self.patient_blocks):
            name = self.patient_names.sample(1).iloc[0]
            self.manual_entries[("{patientFirstName}", "")] = name["First Name"]
            self.manual_entries[("{patientLastName}", "")] = name["Last Name"]
            folder, patient, block_files = self.patient_blocks[self.current_block]
            with open(block_files[0], 'r') as file:
                message = file.read()
            updated_message = self.replace_variables(message, "", "", self.staff_names, self.manual_entries)
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, updated_message)

    def editor_on_entry_focus(self, event, instance, var, entry):
        if entry.get() == var:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT_COLOR)
        message = self.editor_preview_text.get("1.0", tk.END).strip()
        self.editor_highlight_variable(instance, var, message)

    def editor_on_entry_change(self, event, instance, var, entry, file_path):
        value = entry.get()
        self.manual_entries[(var, instance)] = value if value else var
        with open(file_path, 'r') as file:
            message = file.read()
        updated_message = self.replace_variables(message, "", "", self.staff_names, self.manual_entries)
        self.editor_preview_text.delete(1.0, tk.END)
        self.editor_preview_text.insert(tk.END, updated_message)
        self.editor_highlight_variable(instance, var, updated_message)

    def editor_handle_manual_apply(self, choice):
        if choice == "Apply" and 0 <= self.current_block < len(self.patient_blocks):
            folder, patient, block_files = self.patient_blocks[self.current_block]
            edited = {}
            for file_path in block_files:
                with open(file_path, 'r') as file:
                    message = file.read()
                edited[file_path] = self.replace_variables(message, "", "", self.staff_names, self.manual_entries)
            self.edited_messages.update(edited)
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, edited[block_files[0]])
            self.editor_clear_edit_fields()
            self.editor_show_prompt("Save and proceed, reroll, or edit manually?", ["Save", "Reroll", "Manual"], self.editor_handle_post_edit)
        else:
            self.editor_clear_edit_fields()
            self.editor_update_preview()

    def editor_handle_post_edit(self, choice):
        if choice == "Save":
            self.editor_next_block()
        elif choice == "Reroll":
            self.editor_randomize_block()
        elif choice == "Manual":
            self.editor_manual_edit_block()

    def editor_save_and_exit(self):
        for file_path, message in self.edited_messages.items():
            with open(file_path, 'w') as file:
                file.write(message)
        self.root.quit()

    def quit(self):
        if messagebox.askyesno("Confirm Quit", "Changes will not be saved. Are you sure you want to quit?"):
            self.root.quit()

# Define prompts
base_prompts = [
    {"key": "{YYYYMMDD}", "prompt": "Scheduled date of the procedure: (YYYYMMDD)"},
    {"key": "{scheduledTime}", "prompt": "Setup time of the procedure: (HH:MM:SS)"},
    {"key": "{patientLastName}", "prompt": "Patient's last name:"},
    {"key": "{patientFirstName}", "prompt": "Patient's first name:"},
    {"key": "{patientDOB}", "prompt": "Patient's date of birth: (YYYYMMDD)"},
    {"key": "{patientGender}", "prompt": "Patient's gender: (M/F)"},
    {"key": "{patientMRN}", "prompt": "Patient MRN:"},
    {"key": "{duration}", "prompt": "Case duration: Leave blank for random (60-120 min)"},
    {"key": "{procedure}", "prompt": "Procedure name:"},
    {"key": "{procedureDescription}", "prompt": "Procedure description:"},
    {"key": "{specialNeeds}", "prompt": "Special needs:"},
    {"key": "{locationDepartment}", "prompt": "Scheduled Department:"},
    {"key": "{locationOR}", "prompt": "Scheduled OR room:"},
    {"key": "{procedureId}", "prompt": "Procedure ID:"},
    {"key": "{cptCode}", "prompt": "CPT Code:"},
]

procedure_fields = [
    {"key": "{procedure}", "prompt": "Procedure name:"},
    {"key": "{procedureDescription}", "prompt": "Procedure description:"},
    {"key": "{specialNeeds}", "prompt": "Special needs:"},
    {"key": "{locationDepartment}", "prompt": "Scheduled Department:"},
    {"key": "{locationOR}", "prompt": "Scheduled OR room:"},
    {"key": "{procedureId}", "prompt": "Procedure ID:"},
]

if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageApp(root)
    root.mainloop()