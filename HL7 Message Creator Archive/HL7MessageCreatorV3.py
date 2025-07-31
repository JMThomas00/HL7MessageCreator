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

# Default HL7 template without hardcoded AIP segments
default_hl7 = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||SIU^S12|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|S|^^^{YYYYMMDD}{scheduledTime}
ZCS||Y|ORSCH_S14||||49000^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||{patientDOB}|{patientGender}|{patientLastName}^{patientFirstName}^^|||||||||{patientMRN}
PV1||IP|NC-PERIOP^^^NC|||||||GEN|||||||||{patientMRN}
RGS|
OBX|1|DTM|{caseEvent}|In|{YYYYMMDD}{eventTime}|||||||||{YYYYMMDD}{eventTime}||||||||||||||||||
AIS|1||{procedureId}^{procedure}|{YYYYMMDD}{scheduledTime}|0|S|4500|S||||2
NTE|1||{procedureDescription}|Procedure Description|||
NTE|2||{specialNeeds}|Case Notes|||
AIL|1||^{locationOR}^^{locationDepartment}
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
        self.procedure_frame = tk.Frame(self.main_container, bg=BG_COLOR, width=250)
        self.setup_procedure_browser()

        # Separator for resizing
        self.separator = ttk.Separator(self.main_container, orient="vertical")
        self.separator.bind("<B1-Motion>", self.resize_procedure_frame)

        # Main content frame
        self.content_frame = tk.Frame(self.main_container, bg=BG_COLOR)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Preview text box
        self.preview_text = scrolledtext.ScrolledText(self.content_frame, width=80, height=10, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
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
        self.setup_base_prompts()

        # Procedures frame
        self.procedures_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.procedures_frame.pack(fill=tk.X, pady=5)

        # Staff members frame
        self.staff_members_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.staff_members_frame.pack(fill=tk.X, pady=5)

        # Add procedure and staff buttons
        tk.Button(self.content_frame, text="Add Procedure", command=self.add_procedure, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(pady=5)
        tk.Button(self.content_frame, text="Add Staff Member", command=self.add_staff_member, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(pady=5)

        # Create button
        self.create_button = tk.Button(self.content_frame, text="Create", command=self.create_patient, bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 16), activebackground="#3A3C5A")
        self.create_button.pack(pady=10)

        # Initialize state
        self.patients = []
        self.current_patient_index = -1
        self.procedure_panel_visible = False
        self.procedure_frame_width = 250
        self.update_button_states()

    def setup_procedure_browser(self):
        """Set up the procedure browser panel."""
        # Search bar
        search_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_procedures())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Treeview for procedures
        self.tree = ttk.Treeview(self.procedure_frame, show="tree")
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
        # Clear existing items
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
                        self.tree.insert(cat_id, tk.END, text=proc_text, values=(proc["name"], proc["id"], proc["description"], proc["special_needs"]))

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
            if values and len(values) == 4:  # Ensure it's a procedure node
                proc_name, proc_id, proc_desc, proc_needs = values
                if 0 <= self.current_patient_index < len(self.patients):
                    patient = self.patients[self.current_patient_index]
                    patient["base_vars"]["{procedure}"].set(proc_name)
                    patient["base_vars"]["{procedureId}"].set(proc_id)
                    patient["base_vars"]["{procedureDescription}"].set(proc_desc)
                    patient["base_vars"]["{specialNeeds}"].set(proc_needs)
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
            self.update_preview()

    def toggle_procedure_browser(self):
        """Toggle the procedure browser panel."""
        if self.procedure_panel_visible:
            self.procedure_frame.pack_forget()
            self.separator.pack_forget()
            self.procedure_panel_visible = False
        else:
            self.procedure_frame.configure(width=self.procedure_frame_width)
            self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 0))
            self.separator.pack(side=tk.LEFT, fill=tk.Y)
            self.procedure_panel_visible = True

    def resize_procedure_frame(self, event):
        """Handle resizing of the procedure frame."""
        new_width = event.x_root - self.procedure_frame.winfo_rootx()
        if 200 <= new_width <= 400:  # Min 200px, max 400px
            self.procedure_frame_width = new_width
            self.procedure_frame.configure(width=new_width)
            self.procedure_frame.update_idletasks()

    def setup_base_prompts(self):
        """Set up base prompts with entry fields and staff dropdown."""
        # Standard base prompts
        for prompt in base_prompts:
            frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(frame, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.base_entries[prompt['key']] = entry

        # Staff dropdown
        self.staff_collapsed = True
        self.staff_frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
        self.staff_frame.pack(fill=tk.X, pady=5)
        self.staff_toggle_button = tk.Button(
            self.staff_frame, text="Show Staff Members", command=self.toggle_staff_dropdown,
            bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A"
        )
        self.staff_toggle_button.pack(anchor="w", padx=5)

        self.staff_entries_frame = tk.Frame(self.staff_frame, bg=BG_COLOR)
        self.staff_vars = {}
        staff_roles = [
            ("Primary Surgeon", "{primaryFirstName}", "{primaryLastName}", "1.1^Primary", "GEN"),
            ("Circulator", "{firstName}_circ", "{lastName}_circ", "4.20^Circulator", ""),
            ("Scrub", "{firstName}_scrub", "{lastName}_scrub", "4.150^Scrub", ""),
            ("CRNA", "{firstName}_crna", "{lastName}_crna", "2.20^ANE CRNA", ""),
            ("Anesthesiologist", "{firstName}_anes", "{lastName}_anes", "2.139^Anesthesiologist", ""),
        ]

        for role, fname_key, lname_key, _, _ in staff_roles:
            frame = tk.Frame(self.staff_entries_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=role, fg=TEXT_COLOR, bg=BG_COLOR, width=15).pack(side=tk.LEFT, padx=5)
            fname_var = tk.StringVar()
            lname_var = tk.StringVar()
            self.staff_vars[fname_key] = fname_var
            self.staff_vars[lname_key] = lname_var
            fname_entry = UppercaseEntry(frame, textvariable=fname_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=20)
            fname_entry.pack(side=tk.LEFT, padx=5)
            lname_entry = UppercaseEntry(frame, textvariable=lname_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=20)
            lname_entry.pack(side=tk.LEFT, padx=5)
            fname_var.trace_add("write", lambda *args: self.update_preview())
            lname_var.trace_add("write", lambda *args: self.update_preview())

    def toggle_staff_dropdown(self):
        """Toggle the visibility of the staff entries frame."""
        if self.staff_collapsed:
            self.staff_entries_frame.pack(fill=tk.X, padx=5)
            self.staff_toggle_button.config(text="Hide Staff Members")
            self.staff_collapsed = False
        else:
            self.staff_entries_frame.pack_forget()
            self.staff_toggle_button.config(text="Show Staff Members")
            self.staff_collapsed = True

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
            'base_vars': {
                **{prompt['key']: tk.StringVar(value='') for prompt in base_prompts},
                **{key: tk.StringVar(value='') for key in self.staff_vars}
            },
            'procedures': [],
            'staff_members': [],
            'messages': []
        }
        self.patients.append(patient)
        self.current_patient_index = len(self.patients) - 1
        self.load_patient()

    def load_patient(self):
        """Load the current patient's data into the GUI."""
        patient = self.patients[self.current_patient_index]
        for key, entry in self.base_entries.items():
            var = patient['base_vars'].get(key, tk.StringVar())
            patient['base_vars'][key] = var
            entry.config(textvariable=var)
            var.trace_add("write", lambda *args: self.update_preview())
        for key, var in self.staff_vars.items():
            patient_var = patient['base_vars'].get(key, tk.StringVar())
            patient['base_vars'][key] = patient_var
            var.set(patient_var.get())
            patient_var.trace_add("write", lambda *args: self.update_preview())
        for widget in self.procedures_frame.winfo_children():
            widget.destroy()
        for proc in patient['procedures']:
            self.add_procedure_fields(proc)
        for widget in self.staff_members_frame.winfo_children():
            widget.destroy()
        for staff in patient['staff_members']:
            self.add_staff_fields(staff)
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
        """Add a new staff member."""
        staff = {field['key']: tk.StringVar(value='') for field in staff_fields}
        self.patients[self.current_patient_index]['staff_members'].append(staff)
        self.add_staff_fields(staff)

    def add_staff_fields(self, staff):
        """Add entry fields for a staff member."""
        frame = tk.Frame(self.staff_members_frame, bg=BG_COLOR)
        frame.pack(fill=tk.X, pady=5)
        for field in staff_fields:
            subframe = tk.Frame(frame, bg=BG_COLOR)
            subframe.pack(fill=tk.X, pady=2)
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR).pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, textvariable=staff[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            staff[field['key']].trace_add("write", lambda *args: self.update_preview())

    def update_preview(self):
        """Update the preview with the current patient's S12 message."""
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
            base_values = {k: v.get() for k, v in patient['base_vars'].items() if v.get()}
            preview_text = s12_template
            for key, val in base_values.items():
                preview_text = preview_text.replace(key, val)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, preview_text)

    def build_template(self, patient):
        """Build the HL7 template with procedure blocks and dynamic AIP segments."""
        lines = default_hl7.splitlines()
        # Find the start and end of the first procedure block (AIS to AIL)
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("AIS|1|"))
        end_idx = next(i for i, line in enumerate(lines) if line.startswith("AIL|1|"))
        proc_block_template = lines[start_idx:end_idx + 1]
        before_procs = lines[:start_idx]
        after_procs = lines[end_idx + 1:]  # Should be empty

        # Build all procedure blocks
        all_proc_blocks = []
        procedures = [patient] + patient['procedures']  # First 'procedure' is base_vars, others are additional
        for proc_num in range(1, len(procedures) + 1):
            if proc_num == 1:
                proc_values = {k: v.get() for k, v in patient['base_vars'].items()}
            else:
                proc = procedures[proc_num - 1]
                proc_values = {k: v.get() for k, v in proc.items()}
            new_block = []
            for line in proc_block_template:
                if line.startswith("AIS|1|"):
                    new_line = line.replace("AIS|1|", f"AIS|{proc_num}|")
                elif line.startswith("NTE|1|"):
                    nte_num = 2 * proc_num - 1
                    new_line = line.replace("NTE|1|", f"NTE|{nte_num}|")
                elif line.startswith("NTE|2|"):
                    nte_num = 2 * proc_num
                    new_line = line.replace("NTE|2|", f"NTE|{nte_num}|")
                elif line.startswith("AIL|1|"):
                    new_line = line.replace("AIL|1|", f"AIL|{proc_num}|")
                else:
                    new_line = line
                for key, val in proc_values.items():
                    new_line = new_line.replace(key, val)
                new_block.append(new_line)
            all_proc_blocks.extend(new_block)

        # Build staff AIP segments
        aip_lines = []
        staff_roles = [
            ("{primaryLastName}^{primaryFirstName}", "9941778", "1.1^Primary", "GEN"),
            ("{lastName}_circ^{firstName}_circ", "99225747", "4.20^Circulator", ""),
            ("{lastName}_scrub^{firstName}_scrub", "99252693", "4.150^Scrub", ""),
            ("{lastName}_crna^{firstName}_crna", "99252694", "2.20^ANE CRNA", ""),
            ("{lastName}_anes^{firstName}_anes", "99252695", "2.139^Anesthesiologist", ""),
        ]
        for i, (name_template, id_prefix, role, loc) in enumerate(staff_roles, 1):
            aip_line = f"AIP|{i}||{id_prefix}^{name_template}^W^^^^^EPIC^^^^PROVID|{role}|{loc}|{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            aip_lines.append(aip_line)

        # For additional staff members
        for staff in patient['staff_members']:
            staff_values = {k: v.get() for k, v in staff.items() if v.get()}
            role = staff_values.get("role", "Staff")
            last_name = staff_values.get("lastName", "{lastName}")
            first_name = staff_values.get("firstName", "{firstName}")
            i += 1
            aip_line = f"AIP|{i}||99252695^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
            aip_lines.append(aip_line)

        # Combine all parts
        template_lines = before_procs + all_proc_blocks + aip_lines + after_procs
        return "\n".join(template_lines)

    def duplicate_procedure_segments(self, template, proc_num, proc_values):
        """Duplicate AIS through AIL segments for additional procedures."""
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
        
        insert_idx = end_idx + (end_idx - start_idx) * (proc_num - 2)
        lines[insert_idx:insert_idx] = new_block
        return "\n".join(lines)

    def add_staff_segment(self, template, staff_values):
        """Append a new AIP segment."""
        lines = template.splitlines()
        aip_nums = [int(line.split("|")[1]) for line in lines if line.startswith("AIP|")]
        next_num = max(aip_nums, default=0) + 1
        role = staff_values.get("role", "Staff")
        last_name = staff_values.get("lastName", "{lastName}")
        first_name = staff_values.get("firstName", "{firstName}")
        new_aip = f"AIP|{next_num}||99252695^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
        insert_idx = max([i for i, line in enumerate(lines) if line.startswith("AIP|")] + [0]) + 1
        lines.insert(insert_idx, new_aip)
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
        
        # Handle blank or placeholder values
        if base_date == "{YYYYMMDD}" or setup_time == "{scheduledTime}" or not base_date or not setup_time:
            messages = [(template, "00")]
            for i, (event, _) in enumerate(case_events):
                event_replacements = base_values.copy()
                event_replacements["{caseEvent}"] = event
                event_msg = self.fill_template(template, event_replacements)
                messages.append((event_msg, f"{i+1:02}"))
            return messages
        
        # Normalize setup_time (remove colons if present)
        setup_time_clean = setup_time.replace(":", "")
        # Validate date and time
        try:
            datetime.strptime(f"{base_date} {setup_time_clean}", "%Y%m%d %H%M%S")
        except ValueError:
            messages = [(template, "00")]
            for i, (event, _) in enumerate(case_events):
                event_replacements = base_values.copy()
                event_replacements["{caseEvent}"] = event
                event_msg = self.fill_template(template, event_replacements)
                messages.append((event_msg, f"{i+1:02}"))
            return messages
        
        setup_dt = datetime.strptime(f"{base_date} {setup_time_clean}", "%Y%m%d %H%M%S")
        
        messages = []
        event_times = {}
        
        # S12 message (no OBX)
        s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
        s12_time = setup_dt.strftime("%H%M%S")
        s12_replacements = base_values.copy()
        s12_replacements["{eventTime}"] = s12_time
        s12_msg = self.fill_template(s12_template, s12_replacements)
        messages.append((s12_msg, "00"))
        
        # Calculate event times
        for event, offset in case_events:
            event_time = self.get_event_time(setup_dt, offset, duration_min, event_times)
            event_times[event] = event_time
        
        # Generate event messages
        for i, (event, _) in enumerate(case_events):
            event_time = event_times[event]
            time_str = event_time.strftime("%H%M%S")
            date_str = event_time.strftime("%Y%m%d")
            event_replacements = base_values.copy()
            event_replacements["{eventTime}"] = time_str
            event_replacements["{caseEvent}"] = event
            event_replacements["{YYYYMMDD}"] = date_str
            event_msg = self.fill_template(template, event_replacements)
            messages.append((event_msg, f"{i+1:02}"))
        
        return messages

    def create_patient(self):
        """Generate all 15 HL7 messages for the current patient."""
        patient = self.patients[self.current_patient_index]
        template = self.build_template(patient)
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
    {"key": "{YYYYMMDD}", "prompt": "Schedule the date of the procedure? (Format is YYYYMMDD)"},
    {"key": "{scheduledTime}", "prompt": "What's the setup time of the procedure? (Format is HH:MM:SS)"},
    {"key": "{patientLastName}", "prompt": "What's the patient's last name?"},
    {"key": "{patientFirstName}", "prompt": "What's the patient's first name?"},
    {"key": "{patientDOB}", "prompt": "What's the patient's date of birth (YYYYMMDD)?"},
    {"key": "{patientGender}", "prompt": "What's the patient's gender (M/F)"},
    {"key": "{patientMRN}", "prompt": "Enter a new MRN for the patient?"},
    {"key": "{duration}", "prompt": "How long is the case scheduled for? Leave blank for random (60-120 min)"},
    {"key": "{procedure}", "prompt": "What's the procedure name?"},
    {"key": "{procedureDescription}", "prompt": "What's the procedure description?"},
    {"key": "{specialNeeds}", "prompt": "Does this case have any special needs?"},
    {"key": "{locationDepartment}", "prompt": "What department should this be scheduled for?"},
    {"key": "{locationOR}", "prompt": "What OR room should this be scheduled for?"},
    {"key": "{procedureId}", "prompt": "Enter procedure ID (e.g., CPT code, default 49000 if blank)"},
]

procedure_fields = [
    {"key": "{procedure}", "prompt": "What's the procedure name?"},
    {"key": "{procedureDescription}", "prompt": "What's the procedure description?"},
    {"key": "{specialNeeds}", "prompt": "Does this procedure have any special needs?"},
    {"key": "{locationDepartment}", "prompt": "What department should this procedure be scheduled for?"},
    {"key": "{locationOR}", "prompt": "What OR room should this procedure be scheduled for?"},
    {"key": "{procedureId}", "prompt": "Enter procedure ID (e.g., CPT code, default 49000 if blank)"},
]

staff_fields = [
    {"key": "role", "prompt": "What's the staff member's role? (leave blank for 'Staff')"},
    {"key": "lastName", "prompt": "What's the staff member's last name? (leave blank for {lastName})"},
    {"key": "firstName", "prompt": "What's the staff member's first name? (leave blank for {firstName})"},
]

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = HL7MessageCreator(root)
    root.mainloop()