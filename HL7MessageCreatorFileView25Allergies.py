import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import pandas as pd
import random
import os
import re
from datetime import datetime, timedelta
from hl7apy.parser import parse_message
from hl7apy.exceptions import ValidationError

# Color scheme
BG_COLOR = "#1F2139"  # Dark blue-gray background
TEXT_COLOR = "#FFFFFF"  # White text
PREVIEW_BG = "#1E1E1E"  # Near-black for preview areas
TITLE_HL7_MSG = "#465BE7"  # Blue for "HL7 Message" title
TITLE_CREATOR = "#7DCAE3"  # Light blue for "Creator & Editor" title
TITLE_EDITOR = "#7DCAE3"  # Light blue for Editor
DITHERED_TEXT = "#808080"  # Gray for disabled elements or autocompleted text
MATCH_BG = "#2C3DAA"  # Blue for matching procedures (updated)
SELECTED_MATCH_BG = "#465BE7"  # Light blue for selected match (updated)

# Directory setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = SCRIPT_DIR  # CSVs and output in script directory

# Default HL7 template for SIU messages
default_hl7 = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||SIU^{triggerEvent}|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|M|^^^{YYYYMMDD}{scheduledTime}00
ZCS||{addOn}|ORSCH_S14||||{cptCode}^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||{patientDOB}|{patientGender}|{patientLastName}^{patientFirstName}^^|||||||||{patientMRN}
PV1||{encounterType}|NC-PERIOP^^^NC|||||||{specialty}|||||||||{patientMRN}
RGS|
OBX|1|DTM|{caseEvent}|In|{YYYYMMDD}{eventTime}00|||||||||{YYYYMMDD}{eventTime}00||||||||||||||||||
AIS|1||{procedureId}^{procedure}|{YYYYMMDD}{scheduledTime}|0|M|{duration}|M||||2
NTE|1||{procedureDescription}|Procedure Description|||
NTE|2||{specialNeeds}|Case Notes|||
AIL|1||^{locationOR}^^{locationDepartment}
AIP|1||{surgeonID}^{primaryLastName}^{primaryFirstName}^W^^^^^EPIC^^^^PROVID|1.1^Primary|{specialty}|{YYYYMMDD}{scheduledTime}|0|M|{duration}|M
AIP|2||{staffID}^{lastName}^{firstName}^^^^^^EPIC^^^^PROVID|4.20^Circulator||{YYYYMMDD}{scheduledTime}|0|M|{duration}|M
AIP|3||{staffID}^{lastName}^{firstName}^^^^^^^EPIC^^^^PROVID|4.150^Scrub||{YYYYMMDD}{scheduledTime}|0|M|{duration}|M
AIP|4||{staffID}^{lastName}^{firstName}^^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{YYYYMMDD}{scheduledTime}|0|M|{duration}|M
AIP|5||{staffID}^{lastName}^{firstName}^^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{YYYYMMDD}{scheduledTime}|0|M|{duration}|M
"""

# Default HL7 template for ADT messages
adt_template = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||ADT^A01||P|2.5
EVN|A01|{YYYYMMDD}{eventTime}00|
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||{patientDOB}|{patientGender}||||||||||{patientMRN}
PV1||{encounterType}|NC-PERIOP^^^NC||||||||||||||||{patientMRN}|||||||||||||||||||||||||{YYYYMMDD}{eventTime}00
PV2|||||||
{AL1_segments}
"""

# Case events for OBX segments
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

# Default font
DEFAULT_FONT = ("Arial", 10)

# Helper function to validate HHMMSS time format
def is_valid_time(time_str):
    if not time_str:
        return False
    try:
        datetime.strptime(time_str, "%H%M%S")
        return True
    except ValueError:
        return False

# Custom UppercaseEntry widget with dynamic width
class UppercaseEntry(tk.Entry):
    def __init__(self, master, base_width=20, min_width=10, *args, **kwargs):
        self.base_width = base_width
        self.min_width = min_width
        tk.Entry.__init__(self, master, width=base_width, font=DEFAULT_FONT, *args, **kwargs)
        self.bind("<KeyRelease>", self.to_upper)

    def to_upper(self, event):
        current_text = self.get()
        self.delete(0, tk.END)
        self.insert(0, current_text.upper())

    def adjust_width(self, window_width, default_width):
        scale = window_width / default_width
        new_width = max(int(self.base_width * scale), self.min_width)
        self.config(width=new_width)

# Main application class
class HL7MessageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HL7 Message Creator")
        self.root.configure(bg=BG_COLOR)
        self.default_width = 1770
        self.default_height = 1232
        self.root.geometry(f"{self.default_width}x{self.default_height}")
        self.root.minsize(800, 600)
        self.entry_widgets = []
        self.root.bind("<Configure>", self.on_window_resize)

        # Add keyboard shortcuts
        self.root.bind('<Control-n>', lambda event: self.create_new_patient() if self.mode == "Creator" else messagebox.showwarning("Invalid Mode", "New Patient is only available in Creator mode."))
        self.root.bind('<Control-o>', lambda event: self.open_files() if self.mode == "Editor" else messagebox.showwarning("Invalid Mode", "Open File(s) is only available in Editor mode."))
        self.root.bind('<Control-s>', lambda event: self.save_files())
        self.root.bind('<Control-Shift-S>', lambda event: self.save_and_exit())
        self.root.bind('<Control-q>', lambda event: self.quit())
        self.root.bind('<Control-e>', lambda event: self.set_mode("Editor"))
        self.root.bind('<Control-r>', lambda event: self.set_mode("Creator"))

        # Set dark theme for ttk widgets
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=DEFAULT_FONT)
        style.configure("TButton", background=BG_COLOR, foreground=TEXT_COLOR, font=DEFAULT_FONT)
        style.configure("Treeview", background=PREVIEW_BG, foreground=TEXT_COLOR, fieldbackground=PREVIEW_BG, font=DEFAULT_FONT)
        style.map("Treeview", background=[("selected", "#3A3C5A")])
        style.configure("Vertical.TScrollbar", background=BG_COLOR, troughcolor=BG_COLOR, arrowcolor=TEXT_COLOR)

        # Load CSV files
        try:
            self.procedures = pd.read_csv(os.path.join(DATA_DIR, "procedures.csv"))
            self.staff_names = pd.read_csv(os.path.join(DATA_DIR, "staff_names.csv"))
            self.surgeon_names = pd.read_csv(os.path.join(DATA_DIR, "surgeon_names.csv"))
            self.patient_names = pd.read_csv(os.path.join(DATA_DIR, "patient_names.csv"))
            self.allergies = pd.read_csv(os.path.join(DATA_DIR, "allergies.csv"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV files: {e}")
            self.root.quit()
            return

        # Initialize state
        self.patients = []
        self.current_patient_index = -1
        self.procedure_browser_visible = False
        self.allergy_browser_visible = False
        self.procedure_frames = []
        self.folders = ["CurrentDay", "NextDay", "PreviousDay"]
        self.current_block = -1
        self.patient_blocks = []
        self.edited_messages = {}
        self.manual_entries = {}
        self.edit_fields = []
        self.last_mrn = 999  # Starting MRN for random patients
        self.mode = "Creator"  # Track current mode
        self.message_type_radios = []  # To store message type radio buttons
        self.matched_procedures = []  # List to store matched procedure items for navigation
        self.current_match_index = -1  # Index for navigating through matches
        self.autocomplete_suggestion = None  # Store autocomplete suggestion

        # Menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        self.file_menu.add_command(label="New Patient (Ctrl+N)", command=self.create_new_patient)
        self.file_menu.add_command(label="Open File(s) (Ctrl+O)", command=self.open_files)
        self.file_menu.add_command(label="Save (Ctrl+S)", command=self.save_files)
        self.file_menu.add_command(label="Save & Exit (Ctrl+Shift+S)", command=self.save_and_exit)
        self.file_menu.add_command(label="Quit (Ctrl+Q)", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        view_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        view_menu.add_command(label="Creator (Ctrl+R)", command=lambda: self.set_mode("Creator"))
        view_menu.add_command(label="Editor (Ctrl+E)", command=lambda: self.set_mode("Editor"))
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        help_menu = tk.Menu(self.menu_bar, tearoff=0, font=DEFAULT_FONT)
        help_menu.add_command(label="Help", command=self.open_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Content frame
        self.content_frame = tk.Frame(root, bg=BG_COLOR)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Start in Creator mode
        self.set_mode("Creator")

    def on_window_resize(self, event):
        window_width = self.root.winfo_width()
        for entry in self.entry_widgets:
            entry.adjust_width(window_width, self.default_width)

    def set_mode(self, mode):
        self.mode = mode
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        if mode == "Creator":
            self.root.title("HL7 Message Creator")
            self.file_menu.entryconfig("New Patient (Ctrl+N)", state="normal")
            self.file_menu.entryconfig("Open File(s) (Ctrl+O)", state="disabled")
            self.setup_creator()
        elif mode == "Editor":
            self.root.title("HL7 Message Editor")
            self.file_menu.entryconfig("New Patient (Ctrl+N)", state="disabled")
            self.file_menu.entryconfig("Open File(s) (Ctrl+O)", state="normal")
            self.setup_editor()

    def setup_creator(self):
        self.entry_widgets = []
        title_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Creator", font=("Georgia", 32), fg=TITLE_CREATOR, bg=BG_COLOR).pack(side=tk.LEFT)

        self.creator_main_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.creator_main_container.pack(fill=tk.BOTH, expand=True)

        # Left panel frame to hold both procedure and allergy browsers
        self.left_panel_frame = tk.Frame(self.creator_main_container, bg=BG_COLOR, width=350)
        self.left_panel_frame.pack_propagate(False)
        self.left_panel_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # Subframes for procedure and allergy browsers
        self.procedure_browser_frame = tk.Frame(self.left_panel_frame, bg=BG_COLOR)
        self.allergy_browser_frame = tk.Frame(self.left_panel_frame, bg=BG_COLOR)

        # Setup browsers
        self.setup_procedure_browser()
        self.setup_allergy_browser()

        # Initially, show the procedure browser
        self.procedure_browser_frame.pack(fill=tk.BOTH, expand=True)
        self.procedure_browser_visible = True
        self.allergy_browser_visible = False

        self.creator_content_container = tk.Frame(self.creator_main_container, bg=BG_COLOR)
        self.creator_content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.creator_content_container, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.creator_content_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.canvas.create_window((0, 0), window=self.creator_content_frame, anchor="nw")
        self.creator_content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.creator_preview_text = scrolledtext.ScrolledText(
            self.creator_content_frame, width=160, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT
        )
        self.creator_preview_text.pack(fill=tk.X, pady=(0, 10))

        # Top buttons with message type radio buttons
        self.creator_button_frame_top = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.creator_button_frame_top.pack(fill=tk.X, pady=5)
        self.creator_prev_button = tk.Button(self.creator_button_frame_top, text="Previous", command=self.creator_prev_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.creator_prev_button.pack(side=tk.LEFT, padx=5)
        self.creator_next_button = tk.Button(self.creator_button_frame_top, text="Next", command=self.creator_next_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.creator_next_button.pack(side=tk.LEFT, padx=5)
        self.creator_new_patient_button = tk.Button(self.creator_button_frame_top, text="New Patient", command=self.create_new_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.creator_new_patient_button.pack(side=tk.LEFT, padx=5)

        # Message type radio buttons frame
        message_type_frame = tk.Frame(self.creator_button_frame_top, bg=BG_COLOR)
        message_type_frame.pack(side=tk.RIGHT)
        dummy_var = tk.StringVar(value="Scheduled & Case Events")  # Default
        options = ["Scheduled", "Scheduled & Case Events", "Scheduled & Canceled"]
        for option in options:
            rb = tk.Radiobutton(
                message_type_frame, text=option, variable=dummy_var, value=option,
                bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=PREVIEW_BG, font=DEFAULT_FONT
            )
            rb.pack(side=tk.LEFT, padx=5)
            self.message_type_radios.append(rb)

        self.base_prompts_frame = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.base_prompts_frame.pack(fill=tk.X, pady=5)
        self.base_entries = {}
        self.staff_entries = {}
        self.additional_staff = []
        self.additional_surgeons = []
        self.encounter_radios = []  # To store encounter type radio buttons
        self.setup_base_prompts()

        self.procedures_frame = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.procedures_frame.pack(fill=tk.X, pady=5)

        self.creator_button_frame_bottom = tk.Frame(self.creator_content_frame, bg=BG_COLOR)
        self.creator_button_frame_bottom.pack(fill=tk.X, pady=5)
        tk.Button(self.creator_button_frame_bottom, text="Add Surgeon", command=self.add_surgeon, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Remove Last Surgeon", command=self.remove_last_surgeon, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Random Surgeon", command=self.random_surgeon, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Add Staff Member", command=self.add_staff_member, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Remove Last Staff Member", command=self.remove_last_staff_member, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Random Staff", command=self.random_staff, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Browse Procedures", command=self.toggle_procedure_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Add Procedure", command=self.add_procedure, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Remove Last Procedure", command=self.remove_last_procedure, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Random Patient", command=self.random_patient_full, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(self.creator_button_frame_bottom, text="Clear All", command=self.clear_all, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.create_button = tk.Button(self.creator_content_frame, text="Create", command=self.create_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=("Arial", 14))
        self.create_button.pack(pady=10)

        self.creator_update_button_states()
        if self.patients and 0 <= self.current_patient_index < len(self.patients):
            self.creator_load_patient()

    def setup_procedure_browser(self):
        search_frame = tk.Frame(self.procedure_browser_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_procedures())
        self.search_entry = UppercaseEntry(search_frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<Tab>", self.autocomplete_search)
        self.entry_widgets.append(self.search_entry)

        tree_control_frame = tk.Frame(self.procedure_browser_frame, bg=BG_COLOR)
        tree_control_frame.pack(fill=tk.X, pady=5)
        tk.Button(tree_control_frame, text="Collapse All", command=self.collapse_all_procedures, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(tree_control_frame, text="Expand All", command=self.expand_all_procedures, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(tree_control_frame, text="Clear Search", command=self.clear_search, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.RIGHT, padx=5)

        self.tree = ttk.Treeview(self.procedure_browser_frame, show="tree", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.select_procedure)
        self.tree.bind("<<TreeviewSelect>>", self.update_add_button_state)
        self.tree.bind("<Return>", lambda event: self.add_selected_procedure())
        self.tree.bind("<Control-Up>", self.navigate_matches)
        self.tree.bind("<Control-Down>", self.navigate_matches)

        button_frame = tk.Frame(self.procedure_browser_frame, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_procedure_button = tk.Button(button_frame, text="Add Selected Procedure", command=self.add_selected_procedure, fg=DITHERED_TEXT, bg=BG_COLOR, font=DEFAULT_FONT, state="disabled")
        self.add_procedure_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Choose Random", command=self.choose_random_procedure, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Hide Procedures", command=self.toggle_procedure_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.populate_procedure_tree()

    def setup_allergy_browser(self):
        search_frame = tk.Frame(self.allergy_browser_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        self.allergy_search_var = tk.StringVar()
        self.allergy_search_var.trace_add("write", lambda *args: self.filter_allergies())
        self.allergy_search_entry = UppercaseEntry(search_frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, textvariable=self.allergy_search_var)
        self.allergy_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_widgets.append(self.allergy_search_entry)

        self.allergy_tree = ttk.Treeview(self.allergy_browser_frame, show="tree", height=10)
        self.allergy_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.allergy_tree.bind("<Double-1>", self.select_allergy)

        button_frame = tk.Frame(self.allergy_browser_frame, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_allergy_button = tk.Button(button_frame, text="Add Selected Allergy", command=self.add_selected_allergy, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.add_allergy_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Hide Allergies", command=self.toggle_allergy_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.populate_allergy_tree()

    def toggle_procedure_browser(self):
        if self.procedure_browser_visible:
            self.procedure_browser_frame.pack_forget()
            self.procedure_browser_visible = False
        else:
            self.procedure_browser_frame.pack(fill=tk.BOTH, expand=True)
            self.procedure_browser_visible = True

    def toggle_allergy_browser(self):
        if self.allergy_browser_visible:
            self.allergy_browser_frame.pack_forget()
            self.allergy_browser_visible = False
        else:
            self.allergy_browser_frame.pack(fill=tk.BOTH, expand=True)
            self.allergy_browser_visible = True

    def setup_editor(self):
        title_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Editor", font=("Georgia", 32), fg=TITLE_EDITOR, bg=BG_COLOR).pack(side=tk.LEFT)

        self.editor_main_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.editor_main_container.pack(fill=tk.BOTH, expand=True)

        self.editor_button_frame = tk.Frame(self.editor_main_container, bg=BG_COLOR)
        self.editor_button_frame.pack(fill=tk.X, pady=5)
        self.editor_prev_button = tk.Button(self.editor_button_frame, text="Previous", command=self.editor_prev_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_prev_button.pack(side=tk.LEFT, padx=5)
        self.editor_next_button = tk.Button(self.editor_button_frame, text="Next", command=self.editor_next_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_next_button.pack(side=tk.LEFT, padx=5)
        tk.Button(self.editor_button_frame, text="Open File(s)", command=self.open_files, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.editor_content_frame = tk.Frame(self.editor_main_container, bg=BG_COLOR)
        self.editor_content_frame.pack(fill=tk.BOTH, expand=True)

        self.editor_preview_text = scrolledtext.ScrolledText(
            self.editor_content_frame, width=160, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT
        )
        self.editor_preview_text.pack(fill=tk.X, pady=(0, 10))

        self.editor_update_button_states()

    def create_new_patient(self):
        pass  # Placeholder for actual implementation

    def creator_prev_patient(self):
        pass  # Placeholder for actual implementation

    def creator_next_patient(self):
        pass  # Placeholder for actual implementation

    def creator_update_button_states(self):
        pass  # Placeholder for actual implementation

    def creator_load_patient(self):
        pass  # Placeholder for actual implementation

    def open_files(self):
        pass  # Placeholder for actual implementation

    def save_files(self):
        pass  # Placeholder for actual implementation

    def save_and_exit(self):
        pass  # Placeholder for actual implementation

    def quit(self):
        self.root.quit()

    def open_help(self):
        messagebox.showinfo("Help", "Help content goes here.")

    def show_about(self):
        messagebox.showinfo("About", "HL7 Message Creator v1.0")

    def filter_procedures(self):
        pass  # Placeholder for actual implementation

    def autocomplete_search(self, event):
        pass  # Placeholder for actual implementation

    def collapse_all_procedures(self):
        pass  # Placeholder for actual implementation

    def expand_all_procedures(self):
        pass  # Placeholder for actual implementation

    def clear_search(self):
        pass  # Placeholder for actual implementation

    def select_procedure(self, event):
        pass  # Placeholder for actual implementation

    def update_add_button_state(self, event):
        pass  # Placeholder for actual implementation

    def add_selected_procedure(self):
        pass  # Placeholder for actual implementation

    def navigate_matches(self, event):
        pass  # Placeholder for actual implementation

    def choose_random_procedure(self):
        pass  # Placeholder for actual implementation

    def populate_procedure_tree(self):
        pass  # Placeholder for actual implementation

    def filter_allergies(self):
        pass  # Placeholder for actual implementation

    def select_allergy(self, event):
        pass  # Placeholder for actual implementation

    def add_selected_allergy(self):
        pass  # Placeholder for actual implementation

    def populate_allergy_tree(self):
        pass  # Placeholder for actual implementation

    def setup_base_prompts(self):
        self.encounter_radios = []
        dummy_var = tk.StringVar()  # Temporary variable for radio buttons before patient is loaded
        base_prompts = [
            {"prompt": "Date (YYYYMMDD):", "key": "{YYYYMMDD}"},
            {"prompt": "Scheduled Time (HHMMSS):", "key": "{scheduledTime}"},
            {"prompt": "Patient MRN:", "key": "{patientMRN}"},
            {"prompt": "Patient Last Name:", "key": "{patientLastName}"},
            {"prompt": "Patient First Name:", "key": "{patientFirstName}"},
            {"prompt": "Patient DOB (YYYYMMDD):", "key": "{patientDOB}"},
            {"prompt": "Patient Gender (M/F/U):", "key": "{patientGender}"},
            {"prompt": "Encounter Type:", "key": "{encounterType}"},
        ]
        for prompt in base_prompts:
            frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            if prompt['key'] == "{encounterType}":
                radio_frame = tk.Frame(frame, bg=BG_COLOR)
                radio_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                encounter_options = {
                    "Emergent": "E",
                    "Day Surgery": "DS",
                    "Observation": "OBS",
                    "Inpatient": "IP",
                    "Trauma": "T",
                    "Radiology": "Rad"
                }
                for option, code in encounter_options.items():
                    rb = tk.Radiobutton(
                        radio_frame, text=option, variable=dummy_var, value=code,
                        bg=BG_COLOR, fg=TEXT_COLOR, selectcolor=PREVIEW_BG, font=DEFAULT_FONT
                    )
                    rb.pack(side=tk.LEFT, padx=5)
                    self.encounter_radios.append(rb)
            else:
                entry = UppercaseEntry(frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
                entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                self.base_entries[prompt['key']] = entry
                self.entry_widgets.append(entry)

            if prompt['key'] == "{YYYYMMDD}":
                btn_frame = tk.Frame(frame, bg=BG_COLOR)
                btn_frame.pack(side=tk.LEFT, padx=5)
                tk.Button(btn_frame, text="-1 Day", command=lambda: self.adjust_date(-1), fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
                tk.Button(btn_frame, text="Today", command=self.set_today_date, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
                tk.Button(btn_frame, text="+1 Day", command=lambda: self.adjust_date(1), fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            elif prompt['key'] == "{scheduledTime}":
                btn_frame = tk.Frame(frame, bg=BG_COLOR)
                btn_frame.pack(side=tk.LEFT, padx=5)
                self.time_minus_button = tk.Button(btn_frame, text="-1 Hour", command=lambda: self.adjust_time(-1), fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
                self.time_minus_button.pack(side=tk.LEFT, padx=2)
                tk.Button(btn_frame, text="Now", command=self.set_now_time, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
                self.time_plus_button = tk.Button(btn_frame, text="+1 Hour", command=lambda: self.adjust_time(1), fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
                self.time_plus_button.pack(side=tk.LEFT, padx=2)
            elif prompt['key'] == "{patientDOB}":
                btn_frame = tk.Frame(frame, bg=BG_COLOR)
                btn_frame.pack(side=tk.LEFT, padx=5)
                tk.Button(btn_frame, text="Random DOB", command=self.random_dob, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
                tk.Label(btn_frame, text="Age:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
                self.dob_age_var = tk.StringVar()
                age_entry = UppercaseEntry(btn_frame, base_width=5, min_width=5, textvariable=self.dob_age_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
                age_entry.pack(side=tk.LEFT, padx=2)
                self.entry_widgets.append(age_entry)
                tk.Button(btn_frame, text="Add", command=self.set_dob_by_age, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            elif prompt['key'] == "{patientLastName}":
                tk.Button(frame, text="Random Name", command=self.random_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        # Allergies section
        allergies_frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
        allergies_frame.pack(fill=tk.X, pady=5)
        tk.Label(allergies_frame, text="Allergies:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        self.allergies_display = tk.Label(allergies_frame, text="No Known Medical Allergies", fg=TEXT_COLOR, bg=PREVIEW_BG, font=DEFAULT_FONT, anchor="w")
        self.allergies_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(allergies_frame, text="Browse Allergies", command=self.toggle_allergy_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.staff_group_frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
        self.staff_group_frame.pack(fill=tk.X, pady=10)
        self.fixed_roles = [
            {"role": "Primary Surgeon", "code": "1.1^Primary", "last_key": "{primaryLastName}", "first_key": "{primaryFirstName}"},
            {"role": "Circulator", "code": "4.20^Circulator", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Scrub", "code": "4.150^Scrub", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "CRNA", "code": "2.20^ANE CRNA", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Anesthesiologist", "code": "2.139^Anesthesiologist", "last_key": "{lastName}", "first_key": "{firstName}"},
        ]
        for i, role_info in enumerate(self.fixed_roles):
            row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
            row_frame.grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(row_frame, text=f"{role_info['role']}:", fg=TEXT_COLOR, bg=BG_COLOR, width=15, anchor="w", font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            last_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            last_entry.pack(side=tk.LEFT, padx=2)
            tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
            first_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            first_entry.pack(side=tk.LEFT, padx=2)
            last_var = tk.StringVar()
            first_var = tk.StringVar()
            id_var = tk.StringVar(value="{surgeonID}" if role_info["role"] == "Primary Surgeon" else "{staffID}")
            last_entry.config(textvariable=last_var)
            first_entry.config(textvariable=first_var)
            last_var.trace_add("write", lambda *args: self.creator_update_preview())
            first_var.trace_add("write", lambda *args: self.creator_update_preview())
            self.staff_entries[role_info["role"]] = {"lastName": last_var, "firstName": first_var, "id": id_var}
            self.entry_widgets.append(last_entry)
            self.entry_widgets.append(first_entry)

    def editor_prev_patient(self):
        pass  # Placeholder for actual implementation

    def editor_next_patient(self):
        pass  # Placeholder for actual implementation

    def editor_update_button_states(self):
        pass  # Placeholder for actual implementation

    def add_surgeon(self):
        pass  # Placeholder for actual implementation

    def remove_last_surgeon(self):
        pass  # Placeholder for actual implementation

    def random_surgeon(self):
        pass  # Placeholder for actual implementation

    def add_staff_member(self):
        pass  # Placeholder for actual implementation

    def remove_last_staff_member(self):
        pass  # Placeholder for actual implementation

    def random_staff(self):
        pass  # Placeholder for actual implementation

    def add_procedure(self):
        pass  # Placeholder for actual implementation

    def remove_last_procedure(self):
        pass  # Placeholder for actual implementation

    def random_patient_full(self):
        pass  # Placeholder for actual implementation

    def clear_all(self):
        pass  # Placeholder for actual implementation

    def create_patient(self):
        pass  # Placeholder for actual implementation

    def adjust_date(self, days):
        pass  # Placeholder for actual implementation

    def set_today_date(self):
        pass  # Placeholder for actual implementation

    def adjust_time(self, hours):
        pass  # Placeholder for actual implementation

    def set_now_time(self):
        pass  # Placeholder for actual implementation

    def random_dob(self):
        pass  # Placeholder for actual implementation

    def set_dob_by_age(self):
        pass  # Placeholder for actual implementation

    def random_patient(self):
        pass  # Placeholder for actual implementation

    def creator_update_preview(self):
        pass  # Placeholder for actual implementation

if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageApp(root)
    root.mainloop()