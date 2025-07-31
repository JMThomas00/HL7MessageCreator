import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import os
import random
from datetime import datetime, timedelta

# Define color scheme
BG_COLOR = "#1F2139"  # rgb(31, 33, 57)
TEXT_COLOR = "#FFFFFF"  # rgb(255, 255, 255)
PREVIEW_BG = "#1E1E1E"  # rgb(30, 30, 30)
TITLE_HL7_MSG = "#465BE7"  # rgb(70, 91, 231)
TITLE_CREATOR = "#7DCAE3"  # rgb(125, 202, 227)
DITHERED_TEXT = "#808080"  # Gray for disabled buttons

# Get the directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Sample procedure dictionary (~50 procedures, expandable to 300)
procedures = {
    "Orthopedics": {
        "Knee": [
            {
                "name": "Total Knee Arthroplasty",
                "cpt": "27447",
                "id": "ORTHO001",
                "description": "Total knee replacement, right knee, using cemented prosthesis",
                "special_needs": "Requires fluoroscopy, orthopedic implant tray, and tourniquet"
            },
            {
                "name": "ACL Reconstruction",
                "cpt": "29888",
                "id": "ORTHO002",
                "description": "Anterior cruciate ligament reconstruction, left knee, using autograft",
                "special_needs": "Requires arthroscopy equipment and graft fixation devices"
            },
            {
                "name": "Meniscectomy",
                "cpt": "29881",
                "id": "ORTHO003",
                "description": "Partial meniscectomy, medial meniscus, right knee",
                "special_needs": "Requires arthroscopy tower and shaver system"
            }
        ],
        "Hip": [
            {
                "name": "Total Hip Arthroplasty",
                "cpt": "27130",
                "id": "ORTHO004",
                "description": "Total hip replacement, left hip, using uncemented prosthesis",
                "special_needs": "Requires fluoroscopy and hip implant system"
            },
            {
                "name": "Hip Resurfacing",
                "cpt": "27125",
                "id": "ORTHO005",
                "description": "Hip resurfacing, right hip, preserving femoral head",
                "special_needs": "Requires specialized resurfacing implants"
            }
        ],
        "Shoulder": [
            {
                "name": "Rotator Cuff Repair",
                "cpt": "23412",
                "id": "ORTHO006",
                "description": "Open rotator cuff repair, right shoulder",
                "special_needs": "Requires shoulder arthroscopy kit and suture anchors"
            }
        ]
    },
    "Cardiology": {
        "Heart": [
            {
                "name": "Coronary Artery Bypass",
                "cpt": "33533",
                "id": "CARD001",
                "description": "Coronary artery bypass grafting, three vessels, using saphenous vein",
                "special_needs": "Requires cardiopulmonary bypass machine and sternal saw"
            },
            {
                "name": "Pacemaker Insertion",
                "cpt": "33207",
                "id": "CARD002",
                "description": "Permanent pacemaker insertion, dual chamber, right side",
                "special_needs": "Requires electrophysiology suite and pacing leads"
            },
            {
                "name": "Aortic Valve Replacement",
                "cpt": "33405",
                "id": "CARD003",
                "description": "Aortic valve replacement with bioprosthetic valve",
                "special_needs": "Requires heart-lung machine and valve prosthesis"
            }
        ]
    },
    "General Surgery": {
        "Abdomen": [
            {
                "name": "Appendectomy",
                "cpt": "44950",
                "id": "GEN001",
                "description": "Open appendectomy for acute appendicitis",
                "special_needs": "Requires general surgical tray and suction"
            },
            {
                "name": "Cholecystectomy",
                "cpt": "47562",
                "id": "GEN002",
                "description": "Laparoscopic cholecystectomy for gallstones",
                "special_needs": "Requires laparoscopy tower and clip appliers"
            },
            {
                "name": "Hernia Repair",
                "cpt": "49505",
                "id": "GEN003",
                "description": "Inguinal hernia repair, right side, with mesh",
                "special_needs": "Requires mesh and hernia repair kit"
            }
        ],
        "Breast": [
            {
                "name": "Mastectomy",
                "cpt": "19303",
                "id": "GEN004",
                "description": "Simple mastectomy, left breast, for carcinoma",
                "special_needs": "Requires skin-sparing instruments and drains"
            }
        ]
    },
    "Neurosurgery": {
        "Brain": [
            {
                "name": "Craniotomy",
                "cpt": "61510",
                "id": "NEURO001",
                "description": "Craniotomy for tumor resection, left frontal lobe",
                "special_needs": "Requires neuronavigation and craniotomy tray"
            },
            {
                "name": "Ventriculoperitoneal Shunt",
                "cpt": "62223",
                "id": "NEURO002",
                "description": "VP shunt placement for hydrocephalus, right side",
                "special_needs": "Requires shunt kit and stereotactic guidance"
            }
        ],
        "Spine": [
            {
                "name": "Lumbar Fusion",
                "cpt": "22612",
                "id": "NEURO003",
                "description": "Posterior lumbar fusion, L4-L5, with instrumentation",
                "special_needs": "Requires spinal implants and fluoroscopy"
            }
        ]
    },
    "ENT": {
        "Ear": [
            {
                "name": "Tympanoplasty",
                "cpt": "69631",
                "id": "ENT001",
                "description": "Tympanoplasty, right ear, for perforation repair",
                "special_needs": "Requires operating microscope and ear instruments"
            }
        ],
        "Throat": [
            {
                "name": "Tonsillectomy",
                "cpt": "42826",
                "id": "ENT002",
                "description": "Tonsillectomy for chronic tonsillitis",
                "special_needs": "Requires tonsillectomy tray and suction cautery"
            }
        ]
    },
    "Urology": {
        "Kidney": [
            {
                "name": "Nephrectomy",
                "cpt": "50546",
                "id": "URO001",
                "description": "Laparoscopic nephrectomy, left kidney, for renal mass",
                "special_needs": "Requires laparoscopy tower and vascular clamps"
            }
        ],
        "Prostate": [
            {
                "name": "Prostatectomy",
                "cpt": "55866",
                "id": "URO002",
                "description": "Robotic-assisted radical prostatectomy",
                "special_needs": "Requires da Vinci robotic system"
            }
        ]
    },
    "Gynecology": {
        "Uterus": [
            {
                "name": "Hysterectomy",
                "cpt": "58150",
                "id": "GYN001",
                "description": "Total abdominal hysterectomy for fibroids",
                "special_needs": "Requires gynecologic surgical tray and retractors"
            }
        ],
        "Ovaries": [
            {
                "name": "Oophorectomy",
                "cpt": "58940",
                "id": "GYN002",
                "description": "Laparoscopic oophorectomy, right ovary, for cyst",
                "special_needs": "Requires laparoscopy equipment"
            }
        ]
    },
    "Vascular": {
        "Arteries": [
            {
                "name": "Carotid Endarterectomy",
                "cpt": "35301",
                "id": "VASC001",
                "description": "Carotid endarterectomy, left side, for stenosis",
                "special_needs": "Requires vascular shunts and Doppler ultrasound"
            }
        ],
        "Veins": [
            {
                "name": "Varicose Vein Stripping",
                "cpt": "37718",
                "id": "VASC002",
                "description": "Varicose vein stripping, right leg",
                "special_needs": "Requires vein stripper and compression bandages"
            }
        ]
    },
    "Thoracic": {
        "Lung": [
            {
                "name": "Lobectomy",
                "cpt": "32480",
                "id": "THOR001",
                "description": "Right upper lobectomy for lung carcinoma",
                "special_needs": "Requires thoracoscopy equipment and chest tubes"
            }
        ]
    },
    "Podiatry": {
        "Foot": [
            {
                "name": "Nail Removal",
                "cpt": "11730",
                "id": "POD001",
                "description": "Partial nail removal, right foot, great toe, for ingrown nail",
                "special_needs": "Requires podiatric instruments and local anesthesia"
            },
            {
                "name": "Bunionectomy",
                "cpt": "28296",
                "id": "POD002",
                "description": "Bunionectomy, left foot, with osteotomy",
                "special_needs": "Requires fluoroscopy and bone cutting tools"
            }
        ]
    }
}

# Default HL7 template with {cptCode}
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

# Custom UppercaseEntry widget
class UppercaseEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        tk.Entry.__init__(self, *args, **kwargs)
        self.bind("<KeyRelease>", self.to_upper)

    def to_upper(self, event):
        current_text = self.get()
        self.delete(0, tk.END)
        self.insert(0, current_text.upper())

# Main application class
class HL7MessageCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("HL7 Message Creator")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(800, 600)

        # Initialize state
        self.patients = []
        self.current_patient_index = -1
        self.procedure_panel_visible = False

        # Title
        title_container = tk.Frame(self.root, bg=BG_COLOR)
        title_container.pack(pady=10)
        title_frame = tk.Frame(title_container, bg=BG_COLOR)
        title_frame.pack()
        tk.Label(title_frame, text="HL7 Message", font=("Georgia", 32), fg=TITLE_HL7_MSG, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(title_frame, text=" Creator", font=("Georgia", 32), fg=TITLE_CREATOR, bg=BG_COLOR).pack(side=tk.LEFT)

        # Main container for procedure panel and content
        self.main_container = tk.Frame(self.root, bg=BG_COLOR)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Procedure browser panel (hidden initially)
        self.procedure_frame = tk.Frame(self.main_container, bg=BG_COLOR, width=350)
        self.procedure_frame.pack_propagate(False)  # Prevent child widgets from resizing frame
        self.setup_procedure_browser()

        # Main content frame
        self.content_frame = tk.Frame(self.main_container, bg=BG_COLOR)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Preview text box
        self.preview_text = scrolledtext.ScrolledText(self.content_frame, width=160, height=20, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Button frame (centered)
        self.button_container = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.button_container.pack(fill=tk.X)
        self.button_frame = tk.Frame(self.button_container, bg=BG_COLOR)
        self.button_frame.pack(pady=5)

        # Navigation buttons
        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.prev_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A")
        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A")
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Command buttons
        tk.Button(self.button_frame, text="Browse Procedures", command=self.toggle_procedure_browser, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Create New Patient", command=self.create_new_patient, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Quit", command=self.quit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(self.button_frame, text="Save & Exit", command=self.save_and_exit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)

        # Base prompts frame
        self.base_prompts_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.base_prompts_frame.pack(fill=tk.X, pady=5)
        self.base_entries = {}
        self.staff_entries = {}  # Store staff lastName and firstName variables
        self.additional_staff = []  # Track additional staff entries
        self.setup_base_prompts()

        # Procedures frame
        self.procedures_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.procedures_frame.pack(fill=tk.X, pady=5)

        # Add procedure and staff buttons
        tk.Button(self.content_frame, text="Add Procedure", command=self.add_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(pady=5)
        tk.Button(self.content_frame, text="Add Staff Member", command=self.add_staff_member, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(pady=5)

        # Create button
        self.create_button = tk.Button(self.content_frame, text="Create", command=self.create_patient, bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 16), activebackground="#3A3C5A")
        self.create_button.pack(pady=10)

        # Update button states
        self.update_button_states()

    def setup_procedure_browser(self):
        """Set up the procedure browser panel with fixed width and no scrollbar."""
        # Search bar
        search_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_procedures())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Treeview for procedures
        self.tree = ttk.Treeview(self.procedure_frame, show="tree", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<Double-1>", self.select_procedure)

        # Style Treeview
        style = ttk.Style()
        style.configure("Treeview", background=PREVIEW_BG, foreground=TEXT_COLOR, fieldbackground=PREVIEW_BG)
        style.map("Treeview", background=[("selected", "#3A3C5A")])

        # Populate Treeview
        self.populate_procedure_tree()

        # Buttons
        button_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="Choose Random", command=self.choose_random_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=self.toggle_procedure_browser, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)

    def populate_procedure_tree(self, filter_text=""):
        """Populate the Treeview with procedures, recursively filtering."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_text = filter_text.lower()
        for spec in procedures:
            spec_has_match = False
            spec_id = None
            for cat in procedures[spec]:
                cat_has_match = False
                cat_id = None
                for proc in procedures[spec][cat]:
                    proc_text = f"{proc['name']} (CPT: {proc['cpt']})"
                    if not filter_text or (
                        filter_text in spec.lower() or
                        filter_text in cat.lower() or
                        filter_text in proc_text.lower() or
                        filter_text in proc["id"].lower() or
                        filter_text in proc["cpt"].lower()
                    ):
                        if not spec_has_match:
                            spec_id = self.tree.insert("", tk.END, text=spec)
                            spec_has_match = True
                        if not cat_has_match:
                            cat_id = self.tree.insert(spec_id, tk.END, text=cat)
                            cat_has_match = True
                        self.tree.insert(cat_id, tk.END, text=proc_text, values=(proc["name"], proc["id"], proc["description"], proc["special_needs"], proc["cpt"]))

    def filter_procedures(self):
        """Filter procedures based on search input."""
        filter_text = self.search_var.get()
        self.populate_procedure_tree(filter_text)

    def select_procedure(self, event):
        """Handle procedure selection from Treeview."""
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            values = item.get("values")
            if values and len(values) == 5:
                proc_name, proc_id, proc_desc, proc_needs, proc_cpt = values
                if 0 <= self.current_patient_index < len(self.patients):
                    patient = self.patients[self.current_patient_index]
                    patient["base_vars"]["{procedure}"].set(proc_name)
                    patient["base_vars"]["{procedureId}"].set(proc_id)
                    patient["base_vars"]["{procedureDescription}"].set(proc_desc)
                    patient["base_vars"]["{specialNeeds}"].set(proc_needs)
                    patient["base_vars"]["{cptCode}"].set(proc_cpt)
                    self.update_preview()

    def choose_random_procedure(self):
        """Select a random procedure."""
        all_procs = []
        for spec in procedures:
            for cat in procedures[spec]:
                all_procs.extend(procedures[spec][cat])
        if all_procs and 0 <= self.current_patient_index < len(self.patients):
            proc = random.choice(all_procs)
            patient = self.patients[self.current_patient_index]
            patient["base_vars"]["{procedure}"].set(proc["name"])
            patient["base_vars"]["{procedureId}"].set(proc["id"])
            patient["base_vars"]["{procedureDescription}"].set(proc["description"])
            patient["base_vars"]["{specialNeeds}"].set(proc["special_needs"])
            patient["base_vars"]["{cptCode}"].set(proc["cpt"])
            self.update_preview()

    def toggle_procedure_browser(self):
        """Toggle the procedure browser panel."""
        if self.procedure_panel_visible:
            self.procedure_frame.pack_forget()
            self.procedure_panel_visible = False
        else:
            self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
            self.procedure_panel_visible = True

    def setup_base_prompts(self):
        """Set up base prompts and staff group."""
        # Base prompts (excluding staff)
        for prompt in base_prompts:
            frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.base_entries[prompt['key']] = entry

        # Staff group frame
        self.staff_group_frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
        self.staff_group_frame.pack(fill=tk.X, pady=10)

        # Fixed staff roles
        self.fixed_roles = [
            {"role": "Primary Surgeon", "code": "1.1^Primary", "id": "9941778", "last_key": "{primaryLastName}", "first_key": "{primaryFirstName}"},
            {"role": "Circulator", "code": "4.20^Circulator", "id": "99225747", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Scrub", "code": "4.150^Scrub", "id": "99252693", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "CRNA", "code": "2.20^ANE CRNA", "id": "99252694", "last_key": "{lastName}", "first_key": "{firstName}"},
            {"role": "Anesthesiologist", "code": "2.139^Anesthesiologist", "id": "99252695", "last_key": "{lastName}", "first_key": "{firstName}"},
        ]

        # Create staff rows
        for i, role_info in enumerate(self.fixed_roles):
            role = role_info["role"]
            row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
            row_frame.grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(row_frame, text=f"{role}:", fg=TEXT_COLOR, bg=BG_COLOR, width=15, anchor="w").pack(side=tk.LEFT, padx=5)
            tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, width=5).pack(side=tk.LEFT, padx=2)
            last_entry = UppercaseEntry(row_frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
            last_entry.pack(side=tk.LEFT, padx=2)
            tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, width=5).pack(side=tk.LEFT, padx=2)
            first_entry = UppercaseEntry(row_frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
            first_entry.pack(side=tk.LEFT, padx=2)
            # Store StringVars
            last_var = tk.StringVar()
            first_var = tk.StringVar()
            last_entry.config(textvariable=last_var)
            first_entry.config(textvariable=first_var)
            last_var.trace_add("write", lambda *args: self.update_preview())
            first_var.trace_add("write", lambda *args: self.update_preview())
            self.staff_entries[role] = {"lastName": last_var, "firstName": first_var}

    def update_button_states(self):
        """Update Previous and Next button states."""
        if len(self.patients) <= 1:
            self.prev_button.config(state="disabled", fg=DITHERED_TEXT)
            self.next_button.config(state="disabled", fg=DITHERED_TEXT)
        elif self.current_patient_index <= 0:
            self.prev_button.config(state="disabled", fg=DITHERED_TEXT)
            self.next_button.config(state="normal", fg=TEXT_COLOR)
        elif self.current_patient_index >= len(self.patients) - 1:
            self.prev_button.config(state="normal", fg=TEXT_COLOR)
            self.next_button.config(state="disabled", fg=DITHERED_TEXT)
        else:
            self.prev_button.config(state="normal", fg=TEXT_COLOR)
            self.next_button.config(state="normal", fg=TEXT_COLOR)

    def create_new_patient(self):
        """Initialize a new patient and load into GUI."""
        patient = {
            'base_vars': {prompt['key']: tk.StringVar(value='') for prompt in base_prompts},
            'procedures': [],
            'staff_members': [],  # Store additional staff
            'messages': []
        }
        self.patients.append(patient)
        self.current_patient_index = len(self.patients) - 1
        self.load_patient()

    def load_patient(self):
        """Load the current patient's data into the GUI."""
        patient = self.patients[self.current_patient_index]
        # Load base prompts
        for key, entry in self.base_entries.items():
            var = patient['base_vars'][key]
            entry.config(textvariable=var)
            # Remove existing traces to prevent duplicates
            var.trace_remove("write", var.trace_info()[0][1]) if var.trace_info() else None
            var.trace_add("write", lambda *args: self.update_preview())
        # Load staff entries
        for role in self.staff_entries:
            self.staff_entries[role]["lastName"].set("")
            self.staff_entries[role]["firstName"].set("")
        for staff in patient['staff_members']:
            self.add_staff_fields(staff)
        # Clear procedures
        for widget in self.procedures_frame.winfo_children():
            widget.destroy()
        for proc in patient['procedures']:
            self.add_procedure_fields(proc)
        self.update_preview()
        self.update_button_states()

    def add_procedure(self):
        """Add a new procedure."""
        proc = {field['key']: tk.StringVar(value='') for field in procedure_fields}
        self.patients[self.current_patient_index]['procedures'].append(proc)
        self.add_procedure_fields(proc)

    def add_procedure_fields(self, proc):
        """Add entry fields for a procedure."""
        frame = tk.Frame(self.procedures_frame, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=5)
        for field in procedure_fields:
            subframe = tk.Frame(frame, bg=BG_COLOR)
            subframe.pack(fill=tk.X, pady=2)
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, textvariable=proc[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            proc[field['key']].trace_add("write", lambda *args: self.update_preview())

    def add_staff_member(self):
        """Add a new staff member row."""
        staff = {
            "role": tk.StringVar(value="Staff"),
            "lastName": tk.StringVar(value=""),
            "firstName": tk.StringVar(value="")
        }
        self.patients[self.current_patient_index]['staff_members'].append(staff)
        self.add_staff_fields(staff)

    def add_staff_fields(self, staff):
        """Add entry fields for an additional staff member."""
        row = len(self.staff_entries) + len(self.additional_staff)
        row_frame = tk.Frame(self.staff_group_frame, bg=BG_COLOR)
        row_frame.grid(row=row, column=0, sticky="w", pady=2)
        role_entry = UppercaseEntry(row_frame, textvariable=staff["role"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=15)
        role_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(row_frame, text=":", fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT)
        tk.Label(row_frame, text="Last:", fg=TEXT_COLOR, bg=BG_COLOR, width=5).pack(side=tk.LEFT, padx=2)
        last_entry = UppercaseEntry(row_frame, textvariable=staff["lastName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
        last_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="First:", fg=TEXT_COLOR, bg=BG_COLOR, width=5).pack(side=tk.LEFT, padx=2)
        first_entry = UppercaseEntry(row_frame, textvariable=staff["firstName"], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=18)
        first_entry.pack(side=tk.LEFT, padx=2)
        staff["role"].trace_add("write", lambda *args: self.update_preview())
        staff["lastName"].trace_add("write", lambda *args: self.update_preview())
        staff["firstName"].trace_add("write", lambda *args: self.update_preview())
        self.additional_staff.append({"frame": row_frame, "vars": staff})

    def update_preview(self):
        """Update the preview with the current patient's S12 message."""
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            template = self.add_staff_segment(template)  # Ensure staff segments are included
            s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
            base_values = {k: v.get() for k, v in patient['base_vars'].items() if v.get()}
            preview_text = s12_template
            for key, val in base_values.items():
                preview_text = preview_text.replace(key, val)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, preview_text)

    def build_template(self, patient):
        """Build the HL7 template with procedures."""
        template = default_hl7
        procedures = patient['procedures']
        # Add additional procedure segments (AIS, NTE, AIL)
        for i, proc in enumerate(procedures, start=2):
            proc_values = {k: v.get() for k, v in proc.items() if v.get()}
            template = self.add_procedure_segments(template, i, proc_values)
        return template

    def add_procedure_segments(self, template, proc_num, proc_values):
        """Add AIS, NTE, and AIL segments for additional procedures."""
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
        """Generate AIP segments for all staff."""
        lines = template.splitlines()
        # Remove existing AIP segments
        lines = [line for line in lines if not line.startswith("AIP|")]
        insert_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|")) + 1

        # Add fixed role AIP segments
        new_aip_lines = []
        for i, role_info in enumerate(self.fixed_roles, start=1):
            role = role_info["role"]
            code = role_info["code"]
            provider_id = role_info["id"]
            last_key = role_info["last_key"]
            first_key = role_info["first_key"]
            last_name = self.staff_entries[role]["lastName"].get()
            first_name = self.staff_entries[role]["firstName"].get()
            # Preserve placeholders if blank
            last_name = last_name if last_name else last_key
            first_name = first_name if first_name else first_key
            aip_line = f"AIP|{i}||{provider_id}^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|{code}|GEN|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)

        # Add additional staff AIP segments
        aip_count = len(self.fixed_roles)
        for staff in self.patients[self.current_patient_index]['staff_members']:
            aip_count += 1
            role = staff["role"].get() or "Staff"
            last_name = staff["lastName"].get()
            first_name = staff["firstName"].get()
            # Preserve placeholders if blank
            last_name = last_name if last_name else "{lastName}"
            first_name = first_name if first_name else "{firstName}"
            aip_line = f"AIP|{aip_count}||99252695^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            new_aip_lines.append(aip_line)

        lines[insert_idx:insert_idx] = new_aip_lines
        return "\n".join(lines)

    def get_event_time(self, base_time, offset, duration, event_times):
        """Calculate event time with randomness."""
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
        """Fill placeholders in the template."""
        for key, val in replacements.items():
            template = template.replace(key, val)
        return template

    def build_event_messages(self, template, base_values, duration_min):
        """Generate all 15 HL7 messages."""
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
        """Generate all 15 HL7 messages for the current patient."""
        patient = self.patients[self.current_patient_index]
        template = self.build_template(patient)
        template = self.add_staff_segment(template)
        base_values = {k: v.get() for k, v in patient['base_vars'].items()}
        duration_str = base_values.get("{duration}", "")
        duration_min = int(duration_str) if duration_str.isdigit() else random.randint(60, 120)
        messages = self.build_event_messages(template, base_values, duration_min)
        patient['messages'] = messages
        messagebox.showinfo("Patient Created", "Patient messages generated. You can still edit the fields.")

    def prev_patient(self):
        """Go to the previous patient."""
        if self.current_patient_index > 0:
            self.current_patient_index -= 1
            self.load_patient()

    def next_patient(self):
        """Go to the next patient."""
        if self.current_patient_index < len(self.patients) - 1:
            self.current_patient_index += 1
            self.load_patient()

    def quit(self):
        """Quit with confirmation."""
        if messagebox.askyesno("Confirm Quit", "Changes will not be saved. Are you sure you want to quit?"):
            self.root.quit()

    def save_and_exit(self):
        """Save all messages and exit with confirmation."""
        out_dir = os.path.join(SCRIPT_DIR, f"{datetime.now():%y%m%d}-HL7 Output")
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

staff_fields = [
    {"key": "role", "prompt": "Staff member's role:"},
    {"key": "lastName", "prompt": "Staff member's last name: (leave blank for {lastName})"},
    {"key": "firstName", "prompt": "Staff member's first name? (leave blank for {firstName})"},
]

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageCreator(root)
    root.mainloop()