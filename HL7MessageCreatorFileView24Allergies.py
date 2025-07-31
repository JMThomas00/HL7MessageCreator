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
        self.procedure_panel_visible = False
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

    def open_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - User Manual")
        help_window.configure(bg=BG_COLOR)
        help_text = scrolledtext.ScrolledText(
            help_window, width=80, height=30, bg=PREVIEW_BG, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, font=DEFAULT_FONT, wrap=tk.WORD
        )
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Help content with hyperlinks
        help_content = """
HL7 Message Creator and Editor - User Manual

**Table of Contents**
- [Introduction](#introduction)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Getting Started](#getting-started)
- [Creator Mode](#creator-mode)
  - [Creating a New Patient](#creating-a-new-patient)
  - [Filling Patient Details](#filling-patient-details)
  - [Managing Procedures](#managing-procedures)
  - [Managing Allergies](#managing-allergies)
  - [Assigning Staff and Surgeons](#assigning-staff-and-surgeons)
  - [Generating and Saving Messages](#generating-and-saving-messages)
- [Editor Mode](#editor-mode)
  - [Opening HL7 Files](#opening-hl7-files)
  - [Navigating Messages](#navigating-messages)
  - [Editing Messages](#editing-messages)
  - [Saving Changes](#saving-changes)
- [Tips for Effective Use](#tips-for-effective-use)

**Introduction** #introduction
The HL7 Message Creator and Editor is a user-friendly tool designed to generate and modify HL7 messages for healthcare scheduling and case events. It offers two modes: **Creator Mode** for building new messages and **Editor Mode** for modifying existing ones. This manual provides step-by-step guidance to help new users master the application.

**Keyboard Shortcuts** #keyboard-shortcuts
The following shortcuts enhance your workflow:
- **Ctrl+N**: Create a new patient (Creator Mode only)
- **Ctrl+O**: Open HL7 file(s) (Editor Mode only)
- **Ctrl+S**: Save changes
- **Ctrl+Shift+S**: Save and exit
- **Ctrl+Q**: Quit the application
- **Ctrl+E**: Switch to Editor Mode
- **Ctrl+R**: Switch to Creator Mode

**Getting Started** #getting-started
1. Launch the application to enter **Creator Mode** by default.
2. Use the **File** menu or **View** menu to switch between modes or perform actions like saving or quitting.
3. Ensure required CSV files (`procedures.csv`, `staff_names.csv`, `surgeon_names.csv`, `patient_names.csv`, `allergies.csv`) are in the same directory as the script for data population.
4. Familiarize yourself with the interface: the left panel (Creator Mode) includes a procedure browser, while the right panel displays input fields and a preview area.

**Creator Mode** #creator-mode
Creator Mode allows you to generate HL7 messages for new patients.

*Creating a New Patient* #creating-a-new-patient
- Select **File > New Patient** or press **Ctrl+N** to start.
- A blank patient form appears, ready for data entry.
- Use the **Random Patient** button to auto-fill fields with sample data for testing.

*Filling Patient Details* #filling-patient-details
- Enter patient information such as **First Name**, **Last Name**, **Gender**, **DOB**, and **MRN** in the provided fields.
- Use buttons for convenience:
  - **Random Name**: Populate names from `patient_names.csv`.
  - **Random DOB**: Generate a random date of birth.
  - **Age/Add**: Set DOB based on a specified age (0–85).
  - **Date Buttons**: Set the scheduled date to -1 Day, Today, or +1 Day.
  - **Time Buttons**: Adjust the scheduled time by -1 Hour, Now, or +1 Hour.
- Select an **Encounter Type** (e.g., Inpatient, Emergent) via radio buttons.
- Specify the **Message Type** (Scheduled, Scheduled & Case Events, or Scheduled & Canceled) to define the output messages.

*Managing Procedures* #managing-procedures
- Click **Browse Procedures** to open the procedure browser.
- Search or navigate specialties and categories to select a procedure, which auto-fills fields like **Procedure**, **ID**, **CPT Code**, and **Description**.
- Use **Choose Random** in the browser or **Add Procedure** to include additional procedures.
- Remove the last procedure with **Remove Last Procedure** if needed.

*Managing Allergies* #managing-allergies
- Click **Browse Allergies** to open the allergy browser.
- Select allergies from the list to include in the patient's ADT message.
- The selected allergies will be displayed in the Allergies field.

*Assigning Staff and Surgeons* #assigning-staff-and-surgeons
- Assign a **Primary Surgeon** and fixed roles (Circulator, Scrub, CRNA, Anesthesiologist) using the input fields.
- Click **Random Surgeon** or **Random Staff** to populate from `surgeon_names.csv` or `staff_names.csv`.
- Add extra surgeons or staff with **Add Surgeon** or **Add Staff Member**; remove them with **Remove Last Surgeon** or **Remove Last Staff Member**.
- Enter custom roles for additional staff as needed.

*Generating and Saving Messages* #generating-and-saving-messages
- Click **Create** to generate HL7 messages based on the input data and selected message type.
- Preview the generated message in the text area below the input fields.
- Save messages via **File > Save** (Ctrl+S) or **Save & Exit** (Ctrl+Shift+S), selecting an output directory.
- Messages are saved as `.hl7` files, named with the patient’s name and a sequence number (e.g., `JohnDoe-00.hl7`).

**Editor Mode** #editor-mode
Editor Mode is used to modify existing HL7 messages.

*Opening HL7 Files* #opening-hl7-files
- Switch to Editor Mode via **View > Editor** (Ctrl+E).
- Select **File > Open File(s)** (Ctrl+O) to load `.hl7` files from a directory.
- Files are grouped by patient name, with messages sorted for easy navigation.

*Navigating Messages* #navigating-messages
- Use **Previous** and **Next** to cycle through messages within a patient block.
- Use **Previous Patient** and **Next Patient** to switch between patient blocks.
- The context label displays the current patient and message number.

*Editing Messages* #editing-messages
- **Field-Based Editing**: Modify fields like **Patient MRN**, **Location OR**, or **Location Department** in the input area. Changes are reflected in the preview and highlighted in the message text.
- **Direct Edit Mode**: Click **Direct Edit** to manually edit the message text.
  - Make changes directly in the preview area.
  - Save edits to the current message (**Save to Current**) or all messages in the patient block (**Save to All**).
- Apply field-based changes to the current message or all messages in the block using the **Apply** button and selecting **Current** or **All**.

*Saving Changes* #saving-changes
- Save edited messages via **File > Save** (Ctrl+S) or **Save & Exit** (Ctrl+Shift+S).
- Choose an output directory to store the modified `.hl7` files.
- Validation checks are performed during direct edits, with warnings for any HL7 parsing errors.

**Tips for Effective Use** #tips-for-effective-use
- **Validate Inputs**: Ensure fields like dates (YYYYMMDD) and times (HHMMSS) are correctly formatted to avoid errors.
- **Use Random Features**: Leverage random buttons to quickly populate test data during development.
- **Backup Files**: Save frequently to prevent data loss, as unsaved changes are lost on quit (Ctrl+Q).
- **Procedure Browser**: Use the search function to quickly find procedures by name, CPT code, or specialty.
- **Direct Edit Caution**: Be cautious in Direct Edit Mode, as invalid HL7 syntax may cause parsing errors.
- **CSV Maintenance**: Keep CSV files updated with accurate procedure and staff data for reliable randomization.

For further assistance, contact the application support team or refer to the **Help > About** section for version and author details.
"""

        # Dictionary to store section positions
        section_positions = {}

        # Insert content and mark section positions
        lines = help_content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().endswith(')') or line.strip().startswith('- ['):
                # Handle table of contents links
                match = re.match(r'^- \[(.+?)\]\(#(.+?)\)$', line.strip())
                if match:
                    link_text, section_id = match.groups()
                    start_idx = help_text.index(tk.END)
                    help_text.insert(tk.END, line + '\n')
                    end_idx = help_text.index(tk.END)
                    help_text.tag_add(f"link_{section_id}", f"{start_idx}+2c", f"{start_idx}+{len(link_text)+2}c")
                    help_text.tag_configure(f"link_{section_id}", foreground="#7DCAE3", underline=True)
                    help_text.tag_bind(f"link_{section_id}", "<Button-1>", lambda e, sid=section_id: self.scroll_to_section(help_text, section_positions, sid))
                    help_text.tag_bind(f"link_{section_id}", "<Enter>", lambda e, sid=section_id: help_text.config(cursor="hand2"))
                    help_text.tag_bind(f"link_{section_id}", "<Leave>", lambda e: help_text.config(cursor=""))
            elif '#introduction' in line or '#keyboard-shortcuts' in line or '#getting-started' in line or \
                 '#creator-mode' in line or '#creating-a-new-patient' in line or '#filling-patient-details' in line or \
                 '#managing-procedures' in line or '#managing-allergies' in line or '#assigning-staff-and-surgeons' in line or '#generating-and-saving-messages' in line or \
                 '#editor-mode' in line or '#opening-hl7-files' in line or '#navigating-messages' in line or \
                 '#editing-messages' in line or '#saving-changes' in line or '#tips-for-effective-use' in line:
                # Mark section positions
                section_id = line.split('#')[-1].strip()
                section_positions[section_id] = help_text.index(tk.END)
                help_text.insert(tk.END, line + '\n')
            else:
                help_text.insert(tk.END, line + '\n')

        # Make text read-only but allow clicking
        help_text.config(state="disabled")

    def scroll_to_section(self, text_widget, section_positions, section_id):
        """Scroll the text widget to the specified section."""
        if section_id in section_positions:
            text_widget.config(state="normal")
            text_widget.see(section_positions[section_id])
            text_widget.config(state="disabled")

    def show_about(self):
        messagebox.showinfo("About", "HL7 Message Creator\nVersion: 1.0\nAuthor: J.M.Thomas")

    ### File Operations
    def open_files(self):
        if self.mode != "Editor":
            messagebox.showwarning("Invalid Mode", "File opening is only available in Editor mode.")
            return
        files = filedialog.askopenfilenames(
            title="Select HL7 Files",
            filetypes=[("HL7 Files", "*.hl7")],
            initialdir=DATA_DIR
        )
        if files:
            self.patient_blocks = []
            patient_groups = {}
            for file_path in files:
                patient_name = os.path.basename(file_path).split('-')[0]
                patient_groups.setdefault(patient_name, []).append(file_path)
            for patient_name, patient_files in patient_groups.items():
                patient_files.sort()
                messages = []
                for file_path in patient_files:
                    with open(file_path, 'r') as f:
                        message_text = f.read()
                    parsed_values = self.parse_hl7_message(message_text)
                    messages.append({'file_path': file_path, 'message_text': message_text, 'parsed_values': parsed_values})
                self.patient_blocks.append({'patient_name': patient_name, 'messages': messages})
            self.current_patient_index = 0
            self.current_message_index = 0
            self.editor_load_message()

    def save_files(self):
        if self.mode == "Creator":
            self.creator_save_files()
        elif self.mode == "Editor":
            self.editor_save_files()

    def creator_save_files(self):
        out_dir = filedialog.askdirectory(
            title="Select Save Directory",
            initialdir=DATA_DIR,
            mustexist=True
        )
        if not out_dir:
            return
        total_messages = 0
        total_patients = 0
        for patient in self.patients:
            if patient['messages']:
                total_patients += 1
                total_messages += len(patient['messages'])
                base_name = f"{patient['base_vars']['{patientFirstName}'].get() or 'First'}{patient['base_vars']['{patientLastName}'].get() or 'Last'}"
                for msg, idx in patient['messages']:
                    with open(os.path.join(out_dir, f"{base_name}-{idx}.hl7"), 'w') as f:
                        f.write(msg)
        messagebox.showinfo("Save Complete", f"Saved {total_messages} messages for {total_patients} patients to {out_dir}")

    def editor_save_files(self):
        out_dir = filedialog.askdirectory(
            title="Select Save Directory",
            initialdir=DATA_DIR,
            mustexist=True
        )
        if not out_dir:
            return
        total_messages = 0
        for patient_block in self.patient_blocks:
            for message in patient_block['messages']:
                file_path = message['file_path']
                edited_message = self.edited_messages.get(file_path, message['message_text'])
                file_name = os.path.basename(file_path)
                with open(os.path.join(out_dir, file_name), 'w') as f:
                    f.write(edited_message)
                total_messages += 1
        messagebox.showinfo("Save Complete", f"Saved {total_messages} edited messages to {out_dir}")

    def save_and_exit(self):
        self.save_files()
        self.quit()

    def quit(self):
        if messagebox.askyesno("Confirm Quit", "Unsaved changes will be lost. Quit?"):
            self.root.quit()

    ### Date/Time/DOB Methods
    def set_today_date(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            patient["base_vars"]["{YYYYMMDD}"].set(datetime.now().strftime("%Y%m%d"))
            self.creator_update_preview()

    def adjust_date(self, days):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            date_str = patient["base_vars"]["{YYYYMMDD}"].get()
            if date_str == "{YYYYMMDD}" or not date_str:
                return
            try:
                date = datetime.strptime(date_str, "%Y%m%d")
                new_date = date + timedelta(days=days)
                patient["base_vars"]["{YYYYMMDD}"].set(new_date.strftime("%Y%m%d"))
                self.creator_update_preview()
            except ValueError:
                messagebox.showwarning("Invalid Input", "Date must be in YYYYMMDD format.")

    def set_now_time(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            patient["base_vars"]["{scheduledTime}"].set(datetime.now().strftime("%H%M%S"))
            self.update_time_button_states()
            self.creator_update_preview()

    def adjust_time(self, hours):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            time_str = patient["base_vars"]["{scheduledTime}"].get()
            if time_str == "{scheduledTime}" or not time_str:
                return
            try:
                time = datetime.strptime(time_str, "%H%M%S")
                new_time = time + timedelta(hours=hours)
                if 0 <= new_time.hour <= 23:
                    patient["base_vars"]["{scheduledTime}"].set(new_time.strftime("%H%M%S"))
                    self.update_time_button_states()
                    self.creator_update_preview()
                else:
                    messagebox.showwarning("Time Limit", "Time must be between 00:00:00 and 23:59:59.")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Time must be in HHMMSS format.")

    def update_time_button_states(self):
        if 0 <= self.current_patient_index < len(self.patients):
            time_str = self.patients[self.current_patient_index]["base_vars"]["{scheduledTime}"].get()
            if time_str == "{scheduledTime}" or not time_str:
                self.time_minus_button.config(state="normal", fg=TEXT_COLOR)
                self.time_plus_button.config(state="normal", fg=TEXT_COLOR)
                return
            try:
                time = datetime.strptime(time_str, "%H%M%S")
                self.time_minus_button.config(state="disabled" if time.hour == 0 else "normal", fg=DITHERED_TEXT if time.hour == 0 else TEXT_COLOR)
                self.time_plus_button.config(state="disabled" if time.hour == 23 else "normal", fg=DITHERED_TEXT if time.hour == 23 else TEXT_COLOR)
            except ValueError:
                self.time_minus_button.config(state="normal", fg=TEXT_COLOR)
                self.time_plus_button.config(state="normal", fg=TEXT_COLOR)

    def random_dob(self):
        if 0 <= self.current_patient_index < len(self.patients):
            start_date = datetime(1940, 1, 1)
            end_date = datetime(2025, 12, 31)
            days = (end_date - start_date).days
            random_date = start_date + timedelta(days=random.randint(0, days))
            self.patients[self.current_patient_index]["base_vars"]["{patientDOB}"].set(random_date.strftime("%Y%m%d"))
            self.update_dob_age()
            self.creator_update_preview()

    def set_dob_by_age(self):
        if 0 <= self.current_patient_index < len(self.patients):
            age_str = self.dob_age_var.get()
            try:
                age = int(age_str)
                if not 0 <= age <= 85:
                    raise ValueError("Age out of range")
                current_year = datetime.now().year
                birth_year = current_year - age
                month = random.randint(1, 12)
                day = random.randint(1, 28)  # Safe for all months
                dob = datetime(birth_year, month, day)
                self.patients[self.current_patient_index]["base_vars"]["{patientDOB}"].set(dob.strftime("%Y%m%d"))
                self.update_dob_age()
                self.creator_update_preview()
            except ValueError:
                messagebox.showwarning("Invalid Input", "Enter a numeric age between 0 and 85.")

    def update_dob_age(self):
        if 0 <= self.current_patient_index < len(self.patients):
            dob_str = self.patients[self.current_patient_index]["base_vars"]["{patientDOB}"].get()
            if dob_str == "{patientDOB}" or not dob_str:
                self.dob_age_var.set("")
                return
            try:
                dob = datetime.strptime(dob_str, "%Y%m%d")
                today = datetime.now()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                self.dob_age_var.set(str(age))
            except ValueError:
                self.dob_age_var.set("")

    ### Creator Mode
    def setup_creator(self):
        self.entry_widgets = []
        title_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Creator", font=("Georgia", 32), fg=TITLE_CREATOR, bg=BG_COLOR).pack(side=tk.LEFT)

        self.creator_main_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.creator_main_container.pack(fill=tk.BOTH, expand=True)

        self.procedure_frame = tk.Frame(self.creator_main_container, bg=BG_COLOR, width=350)
        self.procedure_frame.pack_propagate(False)
        self.setup_procedure_browser()
        # Ensure procedure panel is open by default
        self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.procedure_panel_visible = True

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
        search_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_procedures())
        self.search_entry = UppercaseEntry(search_frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<Tab>", self.autocomplete_search)
        self.entry_widgets.append(self.search_entry)

        tree_control_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        tree_control_frame.pack(fill=tk.X, pady=5)
        tk.Button(tree_control_frame, text="Collapse All", command=self.collapse_all_procedures, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(tree_control_frame, text="Expand All", command=self.expand_all_procedures, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(tree_control_frame, text="Clear Search", command=self.clear_search, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.RIGHT, padx=5)

        self.tree = ttk.Treeview(self.procedure_frame, show="tree", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.select_procedure)
        self.tree.bind("<<TreeviewSelect>>", self.update_add_button_state)
        self.tree.bind("<Return>", lambda event: self.add_selected_procedure())
        self.tree.bind("<Control-Up>", self.navigate_matches)
        self.tree.bind("<Control-Down>", self.navigate_matches)

        button_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_procedure_button = tk.Button(button_frame, text="Add Selected Procedure", command=self.add_selected_procedure, fg=DITHERED_TEXT, bg=BG_COLOR, font=DEFAULT_FONT, state="disabled")
        self.add_procedure_button.pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Choose Random", command=self.choose_random_procedure, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=self.toggle_procedure_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

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
        self.matched_procedures = []
        self.current_match_index = -1
        self.autocomplete_suggestion = None
        for item in self.tree.get_children():
            self.tree.delete(item)
        search_words = filter_text.lower().split() if filter_text else []
        specialties = self.procedures["specialty"].unique()
        for spec in specialties:
            spec_id = self.tree.insert("", tk.END, text=spec, open=False)
            categories = self.procedures[self.procedures["specialty"] == spec]["category"].unique()
            for cat in categories:
                cat_id = self.tree.insert(spec_id, tk.END, text=cat, open=False)
                procs = self.procedures[(self.procedures["specialty"] == spec) & (self.procedures["category"] == cat)]
                for _, proc in procs.iterrows():
                    proc_text = f"{proc['name']} (CPT: {proc['cpt']})"
                    proc_name_lower = proc["name"].lower()
                    cpt_lower = str(proc["cpt"]).lower()
                    if not search_words or any(word in proc_name_lower or word in cpt_lower for word in search_words):
                        proc_id = self.tree.insert(cat_id, tk.END, text=proc_text, values=(proc["name"], proc["id"], proc["description"], proc["special_needs"], proc["cpt"], spec))
                        if search_words:
                            self.matched_procedures.append(proc_id)
                            # Expand tree to show all matches
                            self.tree.item(spec_id, open=True)
                            self.tree.item(cat_id, open=True)
        if self.matched_procedures:
            self.current_match_index = 0
            self.tree.selection_set(self.matched_procedures[0])
            self.tree.see(self.matched_procedures[0])
            self.highlight_matches()
            if len(self.matched_procedures) == 1:
                self.autocomplete_suggestion = self.tree.item(self.matched_procedures[0], "text").split(" (CPT")[0]
        self.tree.tag_configure("match", background=MATCH_BG, foreground=TEXT_COLOR)
        self.tree.tag_configure("selected_match", background=SELECTED_MATCH_BG, foreground=TEXT_COLOR)

    def filter_procedures(self):
        filter_text = self.search_var.get()
        self.populate_procedure_tree(filter_text)

    def highlight_matches(self):
        for item in self.matched_procedures:
            self.tree.item(item, tags="match")
        if 0 <= self.current_match_index < len(self.matched_procedures):
            self.tree.item(self.matched_procedures[self.current_match_index], tags="selected_match")

    def navigate_matches(self, event):
        if not self.matched_procedures:
            return
        if event.keysym == "Up":
            if self.current_match_index > 0:
                self.current_match_index -= 1
        elif event.keysym == "Down":
            if self.current_match_index < len(self.matched_procedures) - 1:
                self.current_match_index += 1
        self.tree.selection_set(self.matched_procedures[self.current_match_index])
        self.tree.see(self.matched_procedures[self.current_match_index])
        self.highlight_matches()
        self.update_add_button_state(None)

    def autocomplete_search(self, event):
        if self.autocomplete_suggestion and len(self.matched_procedures) == 1:
            current_text = self.search_var.get()
            suggestion = self.autocomplete_suggestion.upper()
            if current_text.upper() != suggestion:
                self.search_var.set(suggestion)
                self.search_entry.selection_range(len(current_text), tk.END)
                self.search_entry.config(fg=DITHERED_TEXT)
                self.root.after(100, lambda: self.search_entry.config(fg=TEXT_COLOR))
                # Focus on tree and select item for Enter to work
                self.tree.focus_set()
                self.tree.selection_set(self.matched_procedures[0])
            return "break"  # Prevent default Tab behavior
        return None

    def select_procedure(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            if values:
                self.apply_procedure_selection(*values)

    def add_selected_procedure(self):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            if values:
                self.apply_procedure_selection(*values)

    def apply_procedure_selection(self, proc_name, proc_id, proc_desc, proc_needs, proc_cpt, proc_specialty):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if not patient["base_vars"]["{procedure}"].get() and not patient["procedures"]:
                patient["base_vars"]["{procedure}"].set(proc_name)
                patient["base_vars"]["{procedureId}"].set(proc_id)
                patient["base_vars"]["{procedureDescription}"].set(proc_desc)
                patient["base_vars"]["{specialNeeds}"].set(proc_needs)
                patient["base_vars"]["{cptCode}"].set(proc_cpt)
                patient['procedure_specialty'].set(proc_specialty)
            else:
                new_proc = {
                    "{procedure}": tk.StringVar(value=proc_name),
                    "{procedureId}": tk.StringVar(value=proc_id),
                    "{procedureDescription}": tk.StringVar(value=proc_desc),
                    "{specialNeeds}": tk.StringVar(value=proc_needs),
                }
                patient["procedures"].append(new_proc)
                self.add_procedure_fields(new_proc)
            self.creator_update_preview()

    def choose_random_procedure(self):
        if 0 <= self.current_patient_index < len(self.patients):
            proc = self.procedures.sample(1).iloc[0]
            patient = self.patients[self.current_patient_index]
            if patient["procedures"]:
                last_proc = patient["procedures"][-1]
                for key, value in zip(["{procedure}", "{procedureId}", "{procedureDescription}", "{specialNeeds}"], [proc["name"], proc["id"], proc["description"], proc["special_needs"]]):
                    last_proc[key].set(value)
            else:
                for key, value in zip(["{procedure}", "{procedureId}", "{procedureDescription}", "{specialNeeds}", "{cptCode}"], [proc["name"], proc["id"], proc["description"], proc["special_needs"], proc["cpt"]]):
                    patient["base_vars"][key].set(value)
                patient['procedure_specialty'].set(proc["specialty"])
            self.creator_update_preview()

    def toggle_procedure_browser(self):
        if self.procedure_panel_visible:
            self.procedure_frame.pack_forget()
            self.procedure_panel_visible = False
        else:
            self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            self.procedure_panel_visible = True

    def clear_search(self):
        self.search_var.set("")
        self.populate_procedure_tree()

    def update_add_button_state(self, event):
        selected = self.tree.selection()
        has_patient = 0 <= self.current_patient_index < len(self.patients)
        self.add_procedure_button.config(
            state="normal" if selected and has_patient else "disabled",
            fg=TEXT_COLOR if selected and has_patient else DITHERED_TEXT
        )

    def setup_base_prompts(self):
        self.encounter_radios = []
        dummy_var = tk.StringVar()  # Temporary variable for radio buttons before patient is loaded
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
        tk.Button(allergies_frame, text="Browse Allergies", command=self.open_allergy_browser, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

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

    def random_patient(self):
        if 0 <= self.current_patient_index < len(self.patients):
            name = self.patient_names.sample(1).iloc[0]
            patient = self.patients[self.current_patient_index]
            patient["base_vars"]["{patientFirstName}"].set(name["First Name"])
            patient["base_vars"]["{patientLastName}"].set(name["Last Name"])
            self.creator_update_preview()

    def random_surgeon(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            surgeon = self.surgeon_names.sample(1).iloc[0]
            self.staff_entries["Primary Surgeon"]["firstName"].set(surgeon["First Name"])
            self.staff_entries["Primary Surgeon"]["lastName"].set(surgeon["Last Name"])
            self.staff_entries["Primary Surgeon"]["id"].set(str(surgeon["ID"]))
            for additional_surgeon in patient['additional_surgeons']:
                additional_surgeon_surgeon = self.surgeon_names.sample(1).iloc[0]
                additional_surgeon["firstName"].set(additional_surgeon_surgeon["First Name"])
                additional_surgeon["lastName"].set(additional_surgeon_surgeon["Last Name"])
                additional_surgeon["id"].set(str(additional_surgeon_surgeon["ID"]))
            self.creator_update_preview()

    def random_staff(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            num_fixed_roles = 4  # Circulator, Scrub, CRNA, Anesthesiologist
            num_additional_staff = len(patient['staff_members'])
            total_roles = num_fixed_roles + num_additional_staff
            if total_roles > len(self.staff_names):
                messagebox.showwarning("Insufficient Staff", "Not enough unique staff members for all roles. Using duplicates.")
                unique_staff = self.staff_names.sample(total_roles, replace=True)
            else:
                unique_staff = self.staff_names.sample(total_roles, replace=False)
            for i, role in enumerate(["Circulator", "Scrub", "CRNA", "Anesthesiologist"]):
                staff = unique_staff.iloc[i]
                self.staff_entries[role]["firstName"].set(staff["First Name"])
                self.staff_entries[role]["lastName"].set(staff["Last Name"])
                self.staff_entries[role]["id"].set(str(staff["ID"]))
            for j, staff_member in enumerate(patient['staff_members']):
                staff = unique_staff.iloc[num_fixed_roles + j]
                staff_member["firstName"].set(staff["First Name"])
                staff_member["lastName"].set(staff["Last Name"])
                staff_member["id"].set(str(staff["ID"]))
            self.creator_update_preview()

    def add_surgeon(self):
        if 0 <= self.current_patient_index < len(self.patients):
            surgeon = {"role": tk.StringVar(value="Assistant Surgeon"), "lastName": tk.StringVar(value=""), "firstName": tk.StringVar(value=""), "id": tk.StringVar(value="{staffID}")}
            self.patients[self.current_patient_index]['additional_surgeons'].append(surgeon)
            self.add_surgeon_fields(surgeon)

    def remove_last_surgeon(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if patient['additional_surgeons']:
                patient['additional_surgeons'].pop()
                self.additional_surgeons[-1]['frame'].destroy()
                self.additional_surgeons.pop()
            else:
                self.staff_entries["Primary Surgeon"]["lastName"].set("")
                self.staff_entries["Primary Surgeon"]["firstName"].set("")
                self.staff_entries["Primary Surgeon"]["id"].set("{surgeonID}")
            self.creator_update_preview()

    def add_staff_member(self):
        if 0 <= self.current_patient_index < len(self.patients):
            staff = {"role": tk.StringVar(value="Staff"), "lastName": tk.StringVar(value=""), "firstName": tk.StringVar(value=""), "id": tk.StringVar(value="{staffID}")}
            self.patients[self.current_patient_index]['staff_members'].append(staff)
            self.add_staff_fields(staff)

    def remove_last_staff_member(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if patient['staff_members']:
                patient['staff_members'].pop()
                self.additional_staff[-1]['frame'].destroy()
                self.additional_staff.pop()
            else:
                for role in ["Circulator", "Scrub", "CRNA", "Anesthesiologist"]:
                    if self.staff_entries[role]["lastName"].get() or self.staff_entries[role]["firstName"].get():
                        self.staff_entries[role]["lastName"].set("")
                        self.staff_entries[role]["firstName"].set("")
                        self.staff_entries[role]["id"].set("{staffID}")
                        return
                if self.staff_entries["Primary Surgeon"]["lastName"].get() or self.staff_entries["Primary Surgeon"]["firstName"].get():
                    self.staff_entries["Primary Surgeon"]["lastName"].set("")
                    self.staff_entries["Primary Surgeon"]["firstName"].set("")
                    self.staff_entries["Primary Surgeon"]["id"].set("{surgeonID}")
            self.creator_update_preview()

    def random_patient_full(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            name = self.patient_names.sample(1).iloc[0]
            first_name = name["First Name"]
            last_name = name["Last Name"]
            patient["base_vars"]["{patientFirstName}"].set(first_name)
            patient["base_vars"]["{patientLastName}"].set(last_name)
            gender = "F" if first_name.lower()[-1] in ['a', 'e', 'i'] else "M"
            patient["base_vars"]["{patientGender}"].set(gender)
            self.random_dob()
            self.last_mrn += 1
            patient["base_vars"]["{patientMRN}"].set(str(self.last_mrn))
            duration = random.randint(60, 120)
            patient["base_vars"]["{duration}"].set(str(duration))
            proc = self.procedures.sample(1).iloc[0]
            patient["base_vars"]["{procedure}"].set(proc["name"])
            patient["base_vars"]["{procedureId}"].set(proc["id"])
            patient["base_vars"]["{procedureDescription}"].set(proc["description"])
            patient["base_vars"]["{specialNeeds}"].set(proc["special_needs"])
            patient["base_vars"]["{cptCode}"].set(proc["cpt"])
            patient['procedure_specialty'].set(proc["specialty"])
            surgeon = self.surgeon_names.sample(1).iloc[0]
            self.staff_entries["Primary Surgeon"]["firstName"].set(surgeon["First Name"])
            self.staff_entries["Primary Surgeon"]["lastName"].set(surgeon["Last Name"])
            self.staff_entries["Primary Surgeon"]["id"].set(str(surgeon["ID"]))
            self.random_staff()  # Call to assign unique staff
            patient["base_vars"]["{YYYYMMDD}"].set(datetime.now().strftime("%Y%m%d"))
            patient["base_vars"]["{scheduledTime}"].set(datetime.now().strftime("%H%M%S"))
            self.creator_update_preview()

    def clear_all(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            for var in patient['base_vars'].values():
                var.set("")
            patient['base_vars']['{encounterType}'].set("IP")  # Reset to default
            patient['message_type'].set("Scheduled & Case Events")  # Reset to default
            for role in self.staff_entries:
                self.staff_entries[role]["lastName"].set("")
                self.staff_entries[role]["firstName"].set("")
                self.staff_entries[role]["id"].set("{surgeonID}" if role == "Primary Surgeon" else "{staffID}")
            for item in self.additional_staff + self.additional_surgeons:
                item['frame'].destroy()
            self.additional_staff = []
            self.additional_surgeons = []
            for frame in self.procedure_frames:
                frame.destroy()
            self.procedure_frames = []
            patient['procedures'] = []
            patient['staff_members'] = []
            patient['additional_surgeons'] = []
            patient['allergies'] = []
            self.update_allergies_display()
            self.creator_update_preview()

    def add_staff_fields(self, staff):
        row = len(self.staff_entries) + len(self.additional_staff)
        row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
        row_frame.grid(row=row, column=0, sticky="w", pady=2)
        role_entry = UppercaseEntry(row_frame, base_width=15, min_width=10, textvariable=staff["role"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        role_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row_frame, text=":", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        last_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, textvariable=staff["lastName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        last_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        first_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, textvariable=staff["firstName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        first_entry.pack(side=tk.LEFT, padx=2)
        for var in [staff["role"], staff["lastName"], staff["firstName"]]:
            var.trace_add("write", lambda *args: self.creator_update_preview())
        self.additional_staff.append({"frame": row_frame, "vars": staff})
        self.entry_widgets.extend([role_entry, last_entry, first_entry])

    def add_surgeon_fields(self, surgeon):
        row = len(self.staff_entries) + len(self.additional_surgeons)
        row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
        row_frame.grid(row=row, column=0, sticky="w", pady=2)
        role_entry = UppercaseEntry(row_frame, base_width=15, min_width=10, textvariable=surgeon["role"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        role_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row_frame, text=":", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        last_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, textvariable=surgeon["lastName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        last_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=2)
        first_entry = UppercaseEntry(row_frame, base_width=18, min_width=10, textvariable=surgeon["firstName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        first_entry.pack(side=tk.LEFT, padx=2)
        for var in [surgeon["role"], surgeon["lastName"], surgeon["firstName"]]:
            var.trace_add("write", lambda *args: self.creator_update_preview())
        self.additional_surgeons.append({"frame": row_frame, "vars": surgeon})
        self.entry_widgets.extend([role_entry, last_entry, first_entry])

    def creator_update_button_states(self):
        total = len(self.patients)
        idx = self.current_patient_index
        self.creator_prev_button.config(state="disabled" if total <= 1 or idx <= 0 else "normal", fg=DITHERED_TEXT if total <= 1 or idx <= 0 else TEXT_COLOR)
        self.creator_next_button.config(state="disabled" if total <= 1 or idx >= total - 1 else "normal", fg=DITHERED_TEXT if total <= 1 or idx >= total - 1 else TEXT_COLOR)
        self.creator_new_patient_button.config(state="normal", fg=TEXT_COLOR)

    def create_new_patient(self):
        if self.mode != "Creator":
            messagebox.showwarning("Invalid Mode", "New Patient is only available in Creator mode.")
            return
        patient = {
            'base_vars': {p['key']: tk.StringVar(value='IP' if p['key'] == '{encounterType}' else '') for p in base_prompts},
            'procedures': [],
            'staff_members': [],
            'additional_surgeons': [],
            'allergies': [],
            'messages': [],
            'procedure_specialty': tk.StringVar(value="GEN"),
            'message_type': tk.StringVar(value="Scheduled & Case Events")  # Default message type
        }
        self.patients.append(patient)
        self.current_patient_index = len(self.patients) - 1
        self.creator_load_patient()

    def creator_load_patient(self):
        patient = self.patients[self.current_patient_index]
        for rb in self.encounter_radios:
            rb.config(variable=patient['base_vars']['{encounterType}'])
        for rb in self.message_type_radios:
            rb.config(variable=patient['message_type'])
        for key, entry in self.base_entries.items():
            var = patient['base_vars'][key]
            entry.config(textvariable=var)
            if var.trace_info():
                var.trace_remove("write", var.trace_info()[0][1])
            var.trace_add("write", lambda *args: self.creator_update_preview())
        patient['message_type'].trace_add("write", lambda *args: self.creator_update_preview())
        for role in self.staff_entries:
            self.staff_entries[role]["lastName"].set("")
            self.staff_entries[role]["firstName"].set("")
            self.staff_entries[role]["id"].set("{surgeonID}" if role == "Primary Surgeon" else "{staffID}")
        for item in self.additional_staff + self.additional_surgeons:
            item['frame'].destroy()
        self.additional_staff = []
        self.additional_surgeons = []
        for staff in patient['staff_members']:
            self.add_staff_fields(staff)
        for surgeon in patient['additional_surgeons']:
            self.add_surgeon_fields(surgeon)
        for widget in self.procedures_frame.winfo_children():
            widget.destroy()
        self.procedure_frames = []
        for proc in patient['procedures']:
            self.add_procedure_fields(proc)
        self.update_allergies_display()
        self.creator_update_preview()
        self.creator_update_button_states()

    def add_procedure(self):
        if 0 <= self.current_patient_index < len(self.patients):
            proc = {f['key']: tk.StringVar(value="") for f in procedure_fields}
            self.patients[self.current_patient_index]['procedures'].append(proc)
            self.add_procedure_fields(proc)
            self.creator_update_preview()

    def remove_last_procedure(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            if patient['procedures']:
                patient['procedures'].pop()
                if self.procedure_frames:
                    self.procedure_frames[-1].destroy()
                    self.procedure_frames.pop()
            else:
                for key in ["{procedure}", "{procedureDescription}", "{specialNeeds}", "{procedureId}", "{cptCode}"]:
                    patient['base_vars'][key].set("")
            self.creator_update_preview()

    def add_procedure_fields(self, proc):
        frame = tk.Frame(self.procedures_frame, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=5)
        self.procedure_frames.append(frame)
        for field in procedure_fields:
            subframe = tk.Frame(frame, bg=BG_COLOR)
            subframe.pack(fill=tk.X, pady=2)
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, base_width=20, min_width=10, textvariable=proc[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            proc[field['key']].trace_add("write", lambda *args: self.creator_update_preview())
            self.entry_widgets.append(entry)

    def open_allergy_browser(self):
        self.allergy_browser_window = tk.Toplevel(self.root)
        self.allergy_browser_window.title("Allergy Browser")
        self.allergy_browser_window.configure(bg=BG_COLOR)
        
        search_frame = tk.Frame(self.allergy_browser_window, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT)
        self.allergy_search_var = tk.StringVar()
        self.allergy_search_var.trace_add("write", lambda *args: self.filter_allergies())
        self.allergy_search_entry = UppercaseEntry(search_frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, textvariable=self.allergy_search_var)
        self.allergy_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.allergy_tree = ttk.Treeview(self.allergy_browser_window, show="tree", height=20)
        self.allergy_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.allergy_tree.bind("<Double-1>", self.select_allergy)
        
        button_frame = tk.Frame(self.allergy_browser_window, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="Add Selected Allergy", command=self.add_selected_allergy, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=self.allergy_browser_window.destroy, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
        
        self.populate_allergy_tree()

    def populate_allergy_tree(self, filter_text=""):
        for item in self.allergy_tree.get_children():
            self.allergy_tree.delete(item)
        search_words = filter_text.lower().split() if filter_text else []
        for _, allergy in self.allergies.iterrows():
            allergy_text = f"{allergy['allergy_name']} (ID: {allergy['allergy_id']})"
            if not search_words or any(word in allergy_text.lower() for word in search_words):
                self.allergy_tree.insert("", tk.END, text=allergy_text, values=(allergy['allergy_id'], allergy['allergy_name'], allergy['reaction'], allergy['severity']))

    def filter_allergies(self):
        filter_text = self.allergy_search_var.get()
        self.populate_allergy_tree(filter_text)

    def select_allergy(self, event):
        item = self.allergy_tree.selection()
        if item:
            values = self.allergy_tree.item(item, "values")
            if values:
                allergy = {"allergyID": values[0], "allergyName": values[1], "allergyReaction": values[2], "allergySeverity": values[3]}
                self.patients[self.current_patient_index]['allergies'].append(allergy)
                self.update_allergies_display()
                self.creator_update_preview()

    def add_selected_allergy(self):
        item = self.allergy_tree.selection()
        if item:
            values = self.allergy_tree.item(item, "values")
            if values:
                allergy = {"allergyID": values[0], "allergyName": values[1], "allergyReaction": values[2], "allergySeverity": values[3]}
                self.patients[self.current_patient_index]['allergies'].append(allergy)
                self.update_allergies_display()
                self.creator_update_preview()

    def update_allergies_display(self):
        if 0 <= self.current_patient_index < len(self.patients):
            allergies = self.patients[self.current_patient_index]['allergies']
            if allergies:
                display_text = ", ".join([allergy['allergyName'] for allergy in allergies])
            else:
                display_text = "No Known Medical Allergies"
            self.allergies_display.config(text=display_text)

    def creator_update_preview(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            template = self.add_staff_segment(template)
            message_type = patient['message_type'].get()
            if message_type == "Scheduled & Case Events":
                preview_template = template  # Full template with OBX for event messages
                trigger_event = "S14"
            else:
                preview_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))  # Without OBX
                trigger_event = "S12" if message_type == "Scheduled" else "S15"
            base_values = {k: v.get() for k, v in patient['base_vars'].items()}
            base_values["{specialty}"] = patient['procedure_specialty'].get()
            preview_text = preview_template
            for key, val in base_values.items():
                if val:
                    preview_text = preview_text.replace(key, val)
            preview_text = preview_text.replace("{triggerEvent}", trigger_event)
            # Add ADT message preview
            al1_segments = []
            if patient['allergies']:
                for i, allergy in enumerate(patient['allergies'], start=1):
                    reaction = allergy['allergyReaction'] if allergy['allergyReaction'] else ""
                    severity = allergy['allergySeverity'] if allergy['allergySeverity'] else ""
                    al1_segment = f"AL1|{i}||{allergy['allergyID']}^{allergy['allergyName']}|{severity}|{reaction}|"
                    al1_segments.append(al1_segment)
            else:
                al1_segments = ["AL1|1||NKA^No Known Allergies||"]
            adt_preview = adt_template.replace("{AL1_segments}", "\n".join(al1_segments))
            for key, val in base_values.items():
                if val:
                    adt_preview = adt_preview.replace(key, val)
            adt_preview = adt_preview.replace("{eventTime}", base_values.get("{scheduledTime}", "{eventTime}"))
            preview_text += "\n\n" + adt_preview
            self.creator_preview_text.delete(1.0, tk.END)
            self.creator_preview_text.insert(tk.END, preview_text)

    def build_template(self, patient):
        template = default_hl7
        for i, proc in enumerate(patient['procedures'], start=2):
            proc_values = {k: v.get() for k, v in proc.items() if v.get()}
            template = self.add_procedure_segments(template, i, proc_values)
        return template

    def add_procedure_segments(self, template, proc_num, proc_values):
        lines = template.splitlines()
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("AIS|1|"))
        end_idx = next(i for i, line in enumerate(lines) if line.startswith("NTE|2|")) + 1
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
            else:
                new_line = line
            for key, val in proc_values.items():
                if val:
                    new_line = new_line.replace(key, val)
            new_block.append(new_line)
        insert_idx = next(i for i, line in enumerate(lines) if line.startswith("NTE|2|")) + 1
        lines[insert_idx:insert_idx] = new_block
        return "\n".join(lines)

    def add_staff_segment(self, template):
        lines = template.splitlines()
        lines = [line for line in lines if not line.startswith("AIP|")]
        insert_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|")) + 1
        new_aip_lines = []
        patient = self.patients[self.current_patient_index]
        specialty = patient['procedure_specialty'].get() if patient['base_vars']['{procedure}'].get() else "GEN"
        primary_last = self.staff_entries["Primary Surgeon"]["lastName"].get() or "{primaryLastName}"
        primary_first = self.staff_entries["Primary Surgeon"]["firstName"].get() or "{primaryFirstName}"
        surgeon_id = self.staff_entries["Primary Surgeon"]["id"].get() or "{surgeonID}"
        aip_line = f"AIP|1||{surgeon_id}^{primary_last}^{primary_first}^W^^^^^EPIC^^^^PROVID|1.1^Primary Surgeon|{specialty}|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
        new_aip_lines.append(aip_line)
        for i, surgeon in enumerate(patient['additional_surgeons'], start=2):
            last_name = surgeon["lastName"].get() or "{lastName}"
            first_name = surgeon["firstName"].get() or "{firstName}"
            staff_id = surgeon["id"].get() or "{staffID}"
            role_code = f"1.{i}^Assistant Surgeon"
            aip_line = f"AIP|{i}||{staff_id}^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|{role_code}|{specialty}|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)
        aip_count = len(patient['additional_surgeons']) + 1
        for role in ["Circulator", "Scrub", "CRNA", "Anesthesiologist"]:
            aip_count += 1
            last_name = self.staff_entries[role]["lastName"].get() or "{lastName}"
            first_name = self.staff_entries[role]["firstName"].get() or "{firstName}"
            staff_id = self.staff_entries[role]["id"].get() or "{staffID}"
            role_info = next(r for r in self.fixed_roles if r["role"] == role)
            aip_line = f"AIP|{aip_count}||{staff_id}^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|{role_info['code']}|GEN|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)
        for staff in patient['staff_members']:
            aip_count += 1
            role = staff["role"].get() or "Staff"
            last_name = staff["lastName"].get() or "{lastName}"
            first_name = staff["firstName"].get() or "{firstName}"
            staff_id = staff["id"].get() or "{staffID}"
            aip_line = f"AIP|{aip_count}||{staff_id}^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)
        lines[insert_idx:insert_idx] = new_aip_lines
        return "\n".join(lines)

    def fill_template(self, template, replacements):
        for key, val in replacements.items():
            if val and val != key:
                template = template.replace(key, val)
        return template

    def build_event_messages(self, template, base_values, duration_min):
        message_type = self.patients[self.current_patient_index]['message_type'].get()
        s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
        event_template = template  # Full template with OBX for event messages
        scheduled_time = base_values.get("{scheduledTime}", "{scheduledTime}")
        is_valid_scheduled_time = is_valid_time(scheduled_time)
        messages = []

        if message_type == "Scheduled":
            replacements = base_values.copy()
            replacements["{triggerEvent}"] = "S12"
            replacements["{eventTime}"] = scheduled_time if is_valid_scheduled_time else "{eventTime}"
            msg = self.fill_template(s12_template, replacements)
            messages.append((msg, "00"))
        elif message_type == "Scheduled & Case Events":
            # S12 message
            replacements = base_values.copy()
            replacements["{triggerEvent}"] = "S12"
            replacements["{eventTime}"] = scheduled_time if is_valid_scheduled_time else "{eventTime}"
            s12_msg = self.fill_template(s12_template, replacements)
            messages.append((s12_msg, "00"))
            # Event messages with S14
            if is_valid_scheduled_time:
                base_dt = datetime.strptime("19700101" + scheduled_time, "%Y%m%d%H%M%S")
                event_dts = {}
                for event_name, offset in case_events:
                    if isinstance(offset, str):
                        if offset.startswith("duration"):
                            parts = offset.split("-")
                            if len(parts) == 2 and parts[1].isdigit():
                                delta = int(parts[1])
                                minutes = duration_min - delta
                            else:
                                minutes = 0
                        else:
                            match = re.match(r"(\w+)([+-]\d+)", offset)
                            if match:
                                base_event, delta_str = match.groups()
                                delta = int(delta_str)
                                if base_event in event_dts:
                                    base_event_dt = event_dts[base_event]
                                    event_dt = base_event_dt + timedelta(minutes=delta + random.randint(-2, 2))
                                    event_dts[event_name] = event_dt
                                    continue
                            minutes = 0
                    else:
                        minutes = offset
                    event_dt = base_dt + timedelta(minutes=minutes + random.randint(-2, 2))
                    event_dts[event_name] = event_dt
                for i, (event_name, _) in enumerate(case_events):
                    event_replacements = base_values.copy()
                    event_replacements["{triggerEvent}"] = "S14"
                    event_replacements["{caseEvent}"] = event_name
                    event_time_str = event_dts[event_name].strftime("%H%M%S")
                    event_replacements["{eventTime}"] = event_time_str
                    event_msg = self.fill_template(event_template, event_replacements)
                    messages.append((event_msg, f"{i+1:02}"))
            else:
                for i, (event_name, _) in enumerate(case_events):
                    event_replacements = base_values.copy()
                    event_replacements["{triggerEvent}"] = "S14"
                    event_replacements["{caseEvent}"] = event_name
                    event_replacements["{eventTime}"] = "{eventTime}"
                    event_msg = self.fill_template(event_template, event_replacements)
                    messages.append((event_msg, f"{i+1:02}"))
        elif message_type == "Scheduled & Canceled":
            replacements = base_values.copy()
            replacements["{eventTime}"] = scheduled_time if is_valid_scheduled_time else "{eventTime}"
            # S12 message
            replacements["{triggerEvent}"] = "S12"
            s12_msg = self.fill_template(s12_template, replacements)
            messages.append((s12_msg, "00"))
            # S15 message
            replacements["{triggerEvent}"] = "S15"
            cancel_msg = self.fill_template(s12_template, replacements)
            messages.append((cancel_msg, "15"))
        return messages

    def create_patient(self):
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            template = self.add_staff_segment(template)
            base_values = {k: v.get() for k, v in patient['base_vars'].items()}
            base_values["{specialty}"] = patient['procedure_specialty'].get()
            duration = base_values.get("{duration}", "")
            duration_min = int(duration) if duration.isdigit() else random.randint(60, 120)
            siu_messages = self.build_event_messages(template, base_values, duration_min)
            patient['messages'] = siu_messages
            # Generate ADT message
            al1_segments = []
            if patient['allergies']:
                for i, allergy in enumerate(patient['allergies'], start=1):
                    reaction = allergy['allergyReaction'] if allergy['allergyReaction'] else ""
                    severity = allergy['allergySeverity'] if allergy['allergySeverity'] else ""
                    al1_segment = f"AL1|{i}||{allergy['allergyID']}^{allergy['allergyName']}|{severity}|{reaction}|"
                    al1_segments.append(al1_segment)
            else:
                al1_segments = ["AL1|1||NKA^No Known Allergies||"]
            adt_message = adt_template.replace("{AL1_segments}", "\n".join(al1_segments))
            for key, val in base_values.items():
                if val:
                    adt_message = adt_message.replace(key, val)
            adt_message = adt_message.replace("{eventTime}", base_values.get("{scheduledTime}", "{eventTime}"))
            patient['messages'].append((adt_message, "ADT"))
            messagebox.showinfo("Success", "Patient messages generated. Edit fields as needed.")

    def creator_prev_patient(self):
        if self.current_patient_index > 0:
            self.current_patient_index -= 1
            self.creator_load_patient()

    def creator_next_patient(self):
        if self.current_patient_index < len(self.patients) - 1:
            self.current_patient_index += 1
            self.creator_load_patient()

    ### Editor Mode
    def setup_editor(self):
        title_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Editor", font=("Georgia", 32), fg=TITLE_EDITOR, bg=BG_COLOR).pack(side=tk.LEFT)

        self.editor_content_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.editor_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.editor_context_label = tk.Label(self.editor_content_frame, text="", fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_context_label.pack(fill=tk.X, pady=5)

        self.editor_input_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.editor_input_frame.pack(fill=tk.X, pady=5)
        self.editor_base_entries = {}
        for prompt in base_prompts:
            frame = tk.Frame(self.editor_input_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(frame, base_width=20, min_width=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.editor_base_entries[prompt['key']] = entry
            self.entry_widgets.append(entry)
            entry.bind("<FocusIn>", lambda e, k=prompt['key']: self.editor_highlight_field(k))
            entry.bind("<KeyRelease>", lambda e, k=prompt['key']: self.editor_update_preview_from_input(k))

        self.apply_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.apply_frame.pack(fill=tk.X, pady=5)
        self.apply_mode = tk.StringVar(value="Current")
        tk.OptionMenu(self.apply_frame, self.apply_mode, "Current", "All").pack(side=tk.LEFT, padx=5)
        tk.Button(self.apply_frame, text="Apply", command=self.editor_apply_changes, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT).pack(side=tk.LEFT, padx=5)

        self.editor_preview_text = scrolledtext.ScrolledText(
            self.editor_content_frame, width=80, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, font=DEFAULT_FONT, state="disabled"
        )
        self.editor_preview_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.direct_edit_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.direct_edit_frame.pack(fill=tk.X, pady=5)
        self.direct_edit_button = tk.Button(self.direct_edit_frame, text="Direct Edit", command=self.toggle_direct_edit, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.direct_edit_button.pack(side=tk.RIGHT, padx=5)
        self.save_current_button = tk.Button(self.direct_edit_frame, text="Save to Current", command=self.save_direct_edit_current, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT, state="disabled")
        self.save_current_button.pack(side=tk.RIGHT, padx=5)
        self.save_all_button = tk.Button(self.direct_edit_frame, text="Save to All", command=self.save_direct_edit_all, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT, state="disabled")
        self.save_all_button.pack(side=tk.RIGHT, padx=5)
        self.direct_edit_mode = False

        self.editor_button_frame = tk.Frame(self.editor_content_frame, bg=BG_COLOR)
        self.editor_button_frame.pack(fill=tk.X, pady=5)
        self.editor_prev_button = tk.Button(self.editor_button_frame, text="Previous", command=self.editor_prev_message, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_prev_button.pack(side=tk.LEFT, padx=5)
        self.editor_next_button = tk.Button(self.editor_button_frame, text="Next", command=self.editor_next_message, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_next_button.pack(side=tk.LEFT, padx=5)
        self.editor_prev_patient_button = tk.Button(self.editor_button_frame, text="Previous Patient", command=self.editor_prev_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_prev_patient_button.pack(side=tk.LEFT, padx=5)
        self.editor_next_patient_button = tk.Button(self.editor_button_frame, text="Next Patient", command=self.editor_next_patient, fg=TEXT_COLOR, bg=BG_COLOR, font=DEFAULT_FONT)
        self.editor_next_patient_button.pack(side=tk.LEFT, padx=5)

        self.loaded_messages = []
        self.current_patient_index = -1
        self.current_message_index = -1
        self.direct_edit_mode = False
        self.message_backups = {}
        self.editor_update_preview()

    def parse_hl7_message(self, message_text):
        parsed_values = {}
        lines = message_text.splitlines()
        for line in lines:
            if line.startswith("AIL"):
                parts = line.split("|")
                if len(parts) > 3:
                    location_parts = parts[3].split("^")
                    if len(location_parts) >= 2:
                        parsed_values["{locationOR}"] = location_parts[1]
                        parsed_values["{locationDepartment}"] = location_parts[3]
            elif line.startswith("PID"):
                parts = line.split("|")
                if len(parts) > 3:
                    parsed_values["{patientMRN}"] = parts[3].split("^")[0]
        return parsed_values

    def editor_load_message(self):
        if 0 <= self.current_patient_index < len(self.patient_blocks) and 0 <= self.current_message_index < len(self.patient_blocks[self.current_patient_index]['messages']):
            message = self.patient_blocks[self.current_patient_index]['messages'][self.current_message_index]
            self.editor_context_label.config(text=f"Patient: {self.patient_blocks[self.current_patient_index]['patient_name']}, Message {self.current_message_index + 1} of {len(self.patient_blocks[self.current_patient_index]['messages'])}")
            self.editor_preview_text.config(state="normal")
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, message['message_text'])
            self.editor_preview_text.config(state="disabled")
            parsed_values = message['parsed_values']
            for key, entry in self.editor_base_entries.items():
                value = parsed_values.get(key, "")
                if value == key:
                    entry.delete(0, tk.END)
                    entry.insert(0, "")
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, value)
        else:
            self.editor_context_label.config(text="No messages loaded")
            self.editor_preview_text.config(state="normal")
            self.editor_preview_text.delete(1.0, tk.END)
            self.editor_preview_text.insert(tk.END, "No patient blocks found.\n")
            self.editor_preview_text.config(state="disabled")

    def editor_update_preview_from_input(self, key):
        value = self.editor_base_entries[key].get()
        message_text = self.editor_preview_text.get("1.0", tk.END).strip()
        message_text = message_text.replace(key, value)
        self.editor_preview_text.config(state="normal")
        self.editor_preview_text.delete(1.0, tk.END)
        self.editor_preview_text.insert(tk.END, message_text)
        self.editor_preview_text.config(state="disabled")
        self.editor_highlight_field(key)

    def editor_highlight_field(self, key):
        self.editor_preview_text.tag_remove("highlight", "1.0", tk.END)
        message = self.editor_preview_text.get("1.0", tk.END).strip()
        field_map = {
            "{locationDepartment}": ("AIL", 3, 2),
            "{locationOR}": ("AIL", 3, 1),
            "{patientMRN}": ("PID", 3, 1),
            # Add more mappings as needed
        }
        if key in field_map:
            segment, field_idx, component_idx = field_map[key]
            for i, line in enumerate(message.splitlines()):
                if line.startswith(segment):
                    parts = line.split("|")
                    if len(parts) > field_idx:
                        field = parts[field_idx]
                        components = field.split("^")
                        if len(components) >= component_idx:
                            value = components[component_idx - 1]
                            start_idx = line.find(value)
                            start_pos = f"{i+1}.{start_idx}"
                            end_pos = f"{i+1}.{start_idx + len(value)}"
                            self.editor_preview_text.tag_add("highlight", start_pos, end_pos)
                            self.editor_preview_text.tag_config("highlight", background="yellow", foreground="black")
                            break

    def editor_apply_changes(self):
        if self.apply_mode.get() == "Current":
            self.apply_to_current_message()
        else:
            self.apply_to_all_messages()

    def apply_to_current_message(self):
        if 0 <= self.current_patient_index < len(self.patient_blocks) and 0 <= self.current_message_index < len(self.patient_blocks[self.current_patient_index]['messages']):
            message = self.patient_blocks[self.current_patient_index]['messages'][self.current_message_index]
            original_text = message['message_text']
            self.message_backups[message['file_path']] = original_text
            updated_text = self.editor_preview_text.get("1.0", tk.END).strip()
            self.edited_messages[message['file_path']] = updated_text
            message['message_text'] = updated_text
            messagebox.showinfo("Applied", "Changes applied to current message")
        else:
            messagebox.showwarning("No Message", "No message selected")

    def apply_to_all_messages(self):
        if 0 <= self.current_patient_index < len(self.patient_blocks):
            patient_block = self.patient_blocks[self.current_patient_index]
            for message in patient_block['messages']:
                original_text = message['message_text']
                self.message_backups[message['file_path']] = original_text
                updated_text = self.editor_preview_text.get("1.0", tk.END).strip()
                self.edited_messages[message['file_path']] = updated_text
                message['message_text'] = updated_text
            messagebox.showinfo("Applied", f"Changes applied to all {len(patient_block['messages'])} messages in this patient block")
        else:
            messagebox.showwarning("No Patient Block", "No patient block selected")

    def toggle_direct_edit(self):
        self.direct_edit_mode = not self.direct_edit_mode
        self.editor_preview_text.config(state="normal" if self.direct_edit_mode else "disabled")
        self.save_current_button.config(state="normal" if self.direct_edit_mode else "disabled", fg=TEXT_COLOR if self.direct_edit_mode else DITHERED_TEXT)
        self.save_all_button.config(state="normal" if self.direct_edit_mode else "disabled", fg=TEXT_COLOR if self.direct_edit_mode else DITHERED_TEXT)
        self.direct_edit_button.config(text="Exit Direct Edit" if self.direct_edit_mode else "Direct Edit")

    def save_direct_edit_current(self):
        if 0 <= self.current_patient_index < len(self.patient_blocks) and 0 <= self.current_message_index < len(self.patient_blocks[self.current_patient_index]['messages']):
            message = self.patient_blocks[self.current_patient_index]['messages'][self.current_message_index]
            original_text = message['message_text']
            self.message_backups[message['file_path']] = original_text
            updated_text = self.editor_preview_text.get("1.0", tk.END).strip()
            try:
                parse_message(updated_text)  # Validate HL7 message
                self.edited_messages[message['file_path']] = updated_text
                message['message_text'] = updated_text
                messagebox.showinfo("Saved", "Direct edits saved to current message")
            except ValidationError as e:
                messagebox.showwarning("Validation Error", f"Invalid HL7 message: {e}")

    def save_direct_edit_all(self):
        if 0 <= self.current_patient_index < len(self.patient_blocks):
            patient_block = self.patient_blocks[self.current_patient_index]
            updated_text = self.editor_preview_text.get("1.0", tk.END).strip()
            try:
                parse_message(updated_text)  # Validate HL7 message
                for message in patient_block['messages']:
                    original_text = message['message_text']
                    self.message_backups[message['file_path']] = original_text
                    self.edited_messages[message['file_path']] = updated_text
                    message['message_text'] = updated_text
                messagebox.showinfo("Saved", f"Direct edits saved to all {len(patient_block['messages'])} messages in this patient block")
            except ValidationError as e:
                messagebox.showwarning("Validation Error", f"Invalid HL7 message: {e}")
        else:
            messagebox.showwarning("No Patient Block", "No patient block selected")

    def editor_prev_message(self):
        if self.current_patient_index >= 0 and self.current_message_index > 0:
            self.current_message_index -= 1
            self.editor_load_message()

    def editor_next_message(self):
        if self.current_patient_index >= 0 and self.current_message_index < len(self.patient_blocks[self.current_patient_index]['messages']) - 1:
            self.current_message_index += 1
            self.editor_load_message()

    def editor_prev_patient(self):
        if self.current_patient_index > 0:
            self.current_patient_index -= 1
            self.current_message_index = 0
            self.editor_load_message()

    def editor_next_patient(self):
        if self.current_patient_index < len(self.patient_blocks) - 1:
            self.current_patient_index += 1
            self.current_message_index = 0
            self.editor_load_message()

    def editor_update_preview(self):
        self.editor_load_message()

# Base prompts and procedure fields
base_prompts = [
    {"prompt": "Patient First Name:", "key": "{patientFirstName}"},
    {"prompt": "Patient Last Name:", "key": "{patientLastName}"},
    {"prompt": "Patient Gender (M/F):", "key": "{patientGender}"},
    {"prompt": "Patient DOB (YYYYMMDD):", "key": "{patientDOB}"},
    {"prompt": "Patient MRN:", "key": "{patientMRN}"},
    {"prompt": "Encounter Type:", "key": "{encounterType}"},
    {"prompt": "Scheduled Date (YYYYMMDD):", "key": "{YYYYMMDD}"},
    {"prompt": "Scheduled Time (HHMMSS):", "key": "{scheduledTime}"},
    {"prompt": "Duration (minutes):", "key": "{duration}"},
    {"prompt": "Procedure:", "key": "{procedure}"},
    {"prompt": "Procedure ID:", "key": "{procedureId}"},
    {"prompt": "CPT Code:", "key": "{cptCode}"},
    {"prompt": "Procedure Description:", "key": "{procedureDescription}"},
    {"prompt": "Special Needs:", "key": "{specialNeeds}"},
    {"prompt": "Location Department:", "key": "{locationDepartment}"},
    {"prompt": "Location OR:", "key": "{locationOR}"},
    {"prompt": "Add On (Y/N):", "key": "{addOn}"},
]

procedure_fields = [
    {"prompt": "Procedure:", "key": "{procedure}"},
    {"prompt": "Procedure ID:", "key": "{procedureId}"},
    {"prompt": "Procedure Description:", "key": "{procedureDescription}"},
    {"prompt": "Special Needs:", "key": "{specialNeeds}"},
]

if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageApp(root)
    root.mainloop()