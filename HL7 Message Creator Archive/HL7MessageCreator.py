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

# Procedure dictionary (150 procedures, unchanged)
procedures = {
    "Orthopedics": {
        "Knee": [
            {"name": "Total Knee Arthroplasty", "cpt": "27447", "id": "ORTHO001", "description": "Total knee replacement, right knee, cemented prosthesis", "special_needs": "Fluoroscopy, orthopedic implant tray, tourniquet"},
            {"name": "ACL Reconstruction", "cpt": "29888", "id": "ORTHO002", "description": "ACL repair, left knee, using autograft", "special_needs": "Arthroscopy equipment, graft fixation"},
            {"name": "Meniscectomy", "cpt": "29881", "id": "ORTHO003", "description": "Partial meniscectomy, medial meniscus, right knee", "special_needs": "Arthroscopy tower, shaver system"},
            {"name": "Knee Arthroscopy", "cpt": "29870", "id": "ORTHO004", "description": "Diagnostic arthroscopy, left knee", "special_needs": "Arthroscopy equipment"},
            {"name": "Patellar Tendon Repair", "cpt": "27380", "id": "ORTHO005", "description": "Patellar tendon repair, right knee", "special_needs": "Suture anchors, knee brace"},
        ],
        "Hip": [
            {"name": "Total Hip Arthroplasty", "cpt": "27130", "id": "ORTHO006", "description": "Total hip replacement, left hip, uncemented", "special_needs": "Fluoroscopy, hip implant system"},
            {"name": "Hip Resurfacing", "cpt": "27125", "id": "ORTHO007", "description": "Hip resurfacing, right hip", "special_needs": "Resurfacing implants"},
            {"name": "Hip Fracture Fixation", "cpt": "27236", "id": "ORTHO008", "description": "Open reduction internal fixation, left femoral neck", "special_needs": "Fluoroscopy, fracture table"},
            {"name": "Labral Repair", "cpt": "29916", "id": "ORTHO009", "description": "Arthroscopic labral repair, right hip", "special_needs": "Arthroscopy tower, suture anchors"},
        ],
        "Shoulder": [
            {"name": "Rotator Cuff Repair", "cpt": "23412", "id": "ORTHO010", "description": "Open rotator cuff repair, right shoulder", "special_needs": "Shoulder arthroscopy kit, suture anchors"},
            {"name": "Shoulder Arthroscopy", "cpt": "29806", "id": "ORTHO011", "description": "Diagnostic arthroscopy, left shoulder", "special_needs": "Arthroscopy equipment"},
            {"name": "Bankart Repair", "cpt": "29807", "id": "ORTHO012", "description": "Arthroscopic Bankart repair, right shoulder", "special_needs": "Arthroscopy tower, anchors"},
        ],
        "Spine": [
            {"name": "Lumbar Discectomy", "cpt": "63030", "id": "ORTHO013", "description": "Microdiscectomy, L5-S1, right side", "special_needs": "Operating microscope, spinal tray"},
            {"name": "Cervical Fusion", "cpt": "22551", "id": "ORTHO014", "description": "Anterior cervical discectomy and fusion, C5-C6", "special_needs": "Fluoroscopy, cervical implants"},
            {"name": "Scoliosis Correction", "cpt": "22800", "id": "ORTHO015", "description": "Posterior spinal fusion for scoliosis", "special_needs": "Spinal instrumentation, neuromonitoring"},
        ],
        "Hand": [
            {"name": "Carpal Tunnel Release", "cpt": "64721", "id": "ORTHO016", "description": "Open carpal tunnel release, right hand", "special_needs": "Hand surgery tray, loupes"},
            {"name": "Trigger Finger Release", "cpt": "26055", "id": "ORTHO017", "description": "Trigger finger release, left ring finger", "special_needs": "Hand instruments, local anesthesia"},
        ],
    },
    "Cardiology": {
        "Heart": [
            {"name": "Coronary Artery Bypass", "cpt": "33533", "id": "CARD001", "description": "CABG, three vessels, saphenous vein graft", "special_needs": "Cardiopulmonary bypass, sternal saw"},
            {"name": "Pacemaker Insertion", "cpt": "33207", "id": "CARD002", "description": "Dual chamber pacemaker, right side", "special_needs": "Electrophysiology suite, pacing leads"},
            {"name": "Aortic Valve Replacement", "cpt": "33405", "id": "CARD003", "description": "Aortic valve replacement, bioprosthetic", "special_needs": "Heart-lung machine, valve prosthesis"},
            {"name": "Mitral Valve Repair", "cpt": "33430", "id": "CARD004", "description": "Mitral valve repair via annuloplasty, left side", "special_needs": "Cardiopulmonary bypass, annuloplasty ring"},
            {"name": "Angioplasty", "cpt": "92920", "id": "CARD005", "description": "Percutaneous coronary angioplasty with stent", "special_needs": "Cath lab, stents"},
        ],
        "Vascular": [
            {"name": "Aortic Aneurysm Repair", "cpt": "33860", "id": "CARD006", "description": "Open repair of ascending aortic aneurysm", "special_needs": "Vascular grafts, cardiopulmonary bypass"},
            {"name": "Endovascular Stent Graft", "cpt": "34705", "id": "CARD007", "description": "EVAR for abdominal aortic aneurysm", "special_needs": "Fluoroscopy, stent graft system"},
        ],
    },
    "General Surgery": {
        "Abdomen": [
            {"name": "Appendectomy", "cpt": "44950", "id": "GEN001", "description": "Open appendectomy for acute appendicitis", "special_needs": "General surgical tray, suction"},
            {"name": "Cholecystectomy", "cpt": "47562", "id": "GEN002", "description": "Laparoscopic cholecystectomy for gallstones", "special_needs": "Laparoscopy tower, clip appliers"},
            {"name": "Hernia Repair", "cpt": "49505", "id": "GEN003", "description": "Inguinal hernia repair, right side, with mesh", "special_needs": "Mesh, hernia repair kit"},
            {"name": "Colectomy", "cpt": "44140", "id": "GEN004", "description": "Partial colectomy, sigmoid colon", "special_needs": "Bowel staplers, retractors"},
            {"name": "Gastrectomy", "cpt": "43620", "id": "GEN005", "description": "Partial gastrectomy for ulcer disease", "special_needs": "GI stapling devices, suction"},
            {"name": "Pancreatectomy", "cpt": "48140", "id": "GEN006", "description": "Distal pancreatectomy for tumor", "special_needs": "Vascular clamps, pancreatic tray"},
        ],
        "Breast": [
            {"name": "Mastectomy", "cpt": "19303", "id": "GEN007", "description": "Simple mastectomy, left breast", "special_needs": "Skin-sparing instruments, drains"},
            {"name": "Lumpectomy", "cpt": "19301", "id": "GEN008", "description": "Lumpectomy, right breast, with sentinel node biopsy", "special_needs": "Dye injection kit, biopsy tools"},
        ],
        "Endocrine": [
            {"name": "Thyroidectomy", "cpt": "60240", "id": "GEN009", "description": "Total thyroidectomy for goiter", "special_needs": "Nerve monitor, fine dissectors"},
            {"name": "Parathyroidectomy", "cpt": "60500", "id": "GEN010", "description": "Parathyroidectomy for adenoma", "special_needs": "Intraoperative PTH monitoring"},
        ],
    },
    "Neurosurgery": {
        "Brain": [
            {"name": "Craniotomy", "cpt": "61510", "id": "NEURO001", "description": "Craniotomy, left frontal lobe tumor", "special_needs": "Neuronavigation, craniotomy tray"},
            {"name": "Ventriculoperitoneal Shunt", "cpt": "62223", "id": "NEURO002", "description": "VP shunt placement, right side", "special_needs": "Shunt kit, stereotactic guidance"},
            {"name": "Aneurysm Clipping", "cpt": "61697", "id": "NEURO003", "description": "Clipping of anterior cerebral artery aneurysm", "special_needs": "Microsurgical clips, operating microscope"},
            {"name": "Deep Brain Stimulation", "cpt": "61867", "id": "NEURO004", "description": "DBS electrode placement, bilateral", "special_needs": "Stereotactic frame, neuromonitoring"},
        ],
        "Spine": [
            {"name": "Lumbar Fusion", "cpt": "22612", "id": "NEURO005", "description": "Posterior lumbar fusion, L4-L5", "special_needs": "Spinal implants, fluoroscopy"},
            {"name": "Cervical Laminectomy", "cpt": "63045", "id": "NEURO006", "description": "Cervical laminectomy, C6-C7", "special_needs": "Spinal tray, neuromonitoring"},
            {"name": "Kyphoplasty", "cpt": "22513", "id": "NEURO007", "description": "Kyphoplasty, T12 vertebra", "special_needs": "Bone cement, fluoroscopy"},
        ],
    },
    "ENT": {
        "Ear": [
            {"name": "Tympanoplasty", "cpt": "69631", "id": "ENT001", "description": "Tympanoplasty, right ear", "special_needs": "Operating microscope, ear instruments"},
            {"name": "Cochlear Implant", "cpt": "69930", "id": "ENT002", "description": "Cochlear implant, left ear", "special_needs": "Implant system, drill"},
            {"name": "Mastoidectomy", "cpt": "69502", "id": "ENT003", "description": "Mastoidectomy, right ear", "special_needs": "High-speed drill, microscope"},
        ],
        "Throat": [
            {"name": "Tonsillectomy", "cpt": "42826", "id": "ENT004", "description": "Tonsillectomy for chronic tonsillitis", "special_needs": "Tonsillectomy tray, suction cautery"},
            {"name": "Laryngectomy", "cpt": "31360", "id": "ENT005", "description": "Total laryngectomy for carcinoma", "special_needs": "Tracheostomy kit, retractors"},
        ],
        "Nose": [
            {"name": "Septoplasty", "cpt": "30520", "id": "ENT006", "description": "Septoplasty for deviated septum", "special_needs": "Nasal speculum, cartilage tools"},
            {"name": "Sinus Surgery", "cpt": "31255", "id": "ENT007", "description": "Endoscopic sinus surgery, bilateral", "special_needs": "Endoscopy tower, microdebrider"},
        ],
    },
    "Urology": {
        "Kidney": [
            {"name": "Nephrectomy", "cpt": "50546", "id": "URO001", "description": "Laparoscopic nephrectomy, left kidney", "special_needs": "Laparoscopy tower, vascular clamps"},
            {"name": "Pyeloplasty", "cpt": "50405", "id": "URO002", "description": "Laparoscopic pyeloplasty, right ureter", "special_needs": "Laparoscopy equipment, stents"},
            {"name": "Kidney Stone Removal", "cpt": "50080", "id": "URO003", "description": "Percutaneous nephrolithotomy, left kidney", "special_needs": "Fluoroscopy, lithotripter"},
        ],
        "Prostate": [
            {"name": "Prostatectomy", "cpt": "55866", "id": "URO004", "description": "Robotic-assisted radical prostatectomy", "special_needs": "da Vinci robotic system"},
            {"name": "TURP", "cpt": "52601", "id": "URO005", "description": "Transurethral resection of prostate", "special_needs": "Resectoscope, irrigation system"},
        ],
        "Bladder": [
            {"name": "Cystectomy", "cpt": "51570", "id": "URO006", "description": "Radical cystectomy with ileal conduit", "special_needs": "Urologic tray, bowel staplers"},
            {"name": "Bladder Suspension", "cpt": "51840", "id": "URO007", "description": "Bladder neck suspension for incontinence", "special_needs": "Suture kit, retractors"},
        ],
    },
    "Gynecology": {
        "Uterus": [
            {"name": "Hysterectomy", "cpt": "58150", "id": "GYN001", "description": "Total abdominal hysterectomy for fibroids", "special_needs": "Gynecologic tray, retractors"},
            {"name": "Myomectomy", "cpt": "58140", "id": "GYN002", "description": "Laparoscopic myomectomy for uterine fibroids", "special_needs": "Laparoscopy tower, morcellator"},
            {"name": "Endometrial Ablation", "cpt": "58353", "id": "GYN003", "description": "Thermal endometrial ablation", "special_needs": "Hysteroscopy equipment, ablation device"},
        ],
        "Ovaries": [
            {"name": "Oophorectomy", "cpt": "58940", "id": "GYN004", "description": "Laparoscopic oophorectomy, right ovary", "special_needs": "Laparoscopy equipment"},
            {"name": "Ovarian Cystectomy", "cpt": "58925", "id": "GYN005", "description": "Laparoscopic cystectomy, left ovary", "special_needs": "Laparoscopy tower, fine dissectors"},
        ],
        "Pelvis": [
            {"name": "Pelvic Floor Repair", "cpt": "57268", "id": "GYN006", "description": "Vaginal repair of enterocele", "special_needs": "Pelvic surgery kit, mesh"},
            {"name": "Laparoscopic Salpingectomy", "cpt": "58700", "id": "GYN007", "description": "Bilateral salpingectomy", "special_needs": "Laparoscopy equipment"},
        ],
    },
    "Vascular": {
        "Arteries": [
            {"name": "Carotid Endarterectomy", "cpt": "35301", "id": "VASC001", "description": "Carotid endarterectomy, left side", "special_needs": "Vascular shunts, Doppler ultrasound"},
            {"name": "Femoral Bypass", "cpt": "35556", "id": "VASC002", "description": "Femoral-popliteal bypass, right leg", "special_needs": "Vascular grafts, clamps"},
            {"name": "Angiogram", "cpt": "36200", "id": "VASC003", "description": "Diagnostic angiogram, lower extremities", "special_needs": "Cath lab, contrast dye"},
        ],
        "Veins": [
            {"name": "Varicose Vein Stripping", "cpt": "37718", "id": "VASC004", "description": "Varicose vein stripping, right leg", "special_needs": "Vein stripper, compression bandages"},
            {"name": "Sclerotherapy", "cpt": "36470", "id": "VASC005", "description": "Sclerotherapy for spider veins, bilateral", "special_needs": "Sclerosant, ultrasound guidance"},
        ],
    },
    "Thoracic": {
        "Lung": [
            {"name": "Lobectomy", "cpt": "32480", "id": "THOR001", "description": "Right upper lobectomy for carcinoma", "special_needs": "Thoracoscopy equipment, chest tubes"},
            {"name": "Pneumonectomy", "cpt": "32440", "id": "THOR002", "description": "Left pneumonectomy for tumor", "special_needs": "Thoracic tray, staplers"},
            {"name": "Wedge Resection", "cpt": "32505", "id": "THOR003", "description": "VATS wedge resection, right lung", "special_needs": "VATS equipment, endostaplers"},
        ],
        "Esophagus": [
            {"name": "Esophagectomy", "cpt": "43107", "id": "THOR004", "description": "Transhiatal esophagectomy", "special_needs": "GI staplers, retractors"},
            {"name": "Nissen Fundoplication", "cpt": "43280", "id": "THOR005", "description": "Laparoscopic fundoplication for GERD", "special_needs": "Laparoscopy tower, suture kit"},
        ],
    },
    "Podiatry": {
        "Foot": [
            {"name": "Nail Removal", "cpt": "11730", "id": "POD001", "description": "Partial nail removal, right foot, great toe", "special_needs": "Podiatric instruments, local anesthesia"},
            {"name": "Bunionectomy", "cpt": "28296", "id": "POD002", "description": "Bunionectomy, left foot, with osteotomy", "special_needs": "Fluoroscopy, bone cutting tools"},
            {"name": "Hammertoe Correction", "cpt": "28285", "id": "POD003", "description": "Hammertoe correction, right second toe", "special_needs": "K-wires, podiatric tray"},
            {"name": "Plantar Fasciotomy", "cpt": "28060", "id": "POD004", "description": "Plantar fasciotomy, left foot", "special_needs": "Scalpel, imaging guidance"},
        ],
        "Ankle": [
            {"name": "Ankle Arthroscopy", "cpt": "29891", "id": "POD005", "description": "Diagnostic arthroscopy, right ankle", "special_needs": "Arthroscopy equipment"},
            {"name": "Achilles Tendon Repair", "cpt": "27650", "id": "POD006", "description": "Achilles tendon repair, left ankle", "special_needs": "Suture anchors, tendon kit"},
        ],
    },
    "Plastic Surgery": {
        "Reconstructive": [
            {"name": "Skin Graft", "cpt": "15100", "id": "PLAST001", "description": "Split-thickness skin graft, left thigh", "special_needs": "Dermatome, graft mesher"},
            {"name": "Flap Reconstruction", "cpt": "15738", "id": "PLAST002", "description": "Local flap reconstruction, right cheek", "special_needs": "Microsurgical instruments, doppler"},
            {"name": "Breast Reconstruction", "cpt": "19357", "id": "PLAST003", "description": "Breast reconstruction with implant, left side", "special_needs": "Tissue expanders, implants"},
        ],
        "Cosmetic": [
            {"name": "Rhinoplasty", "cpt": "30410", "id": "PLAST004", "description": "Open rhinoplasty for nasal deformity", "special_needs": "Nasal instruments, cartilage grafts"},
            {"name": "Facelift", "cpt": "15824", "id": "PLAST005", "description": "Rhytidectomy for facial rejuvenation", "special_needs": "Fine suture kit, loupes"},
            {"name": "Liposuction", "cpt": "15877", "id": "PLAST006", "description": "Liposuction, abdominal region", "special_needs": "Suction cannula, tumescent solution"},
        ],
    },
    "Ophthalmology": {
        "Eye": [
            {"name": "Cataract Surgery", "cpt": "66984", "id": "OPHT001", "description": "Phacoemulsification, right eye, with IOL", "special_needs": "Phaco machine, intraocular lens"},
            {"name": "Glaucoma Surgery", "cpt": "66170", "id": "OPHT002", "description": "Trabeculectomy, left eye", "special_needs": "Microsurgical instruments, mitomycin-C"},
            {"name": "Corneal Transplant", "cpt": "65730", "id": "OPHT003", "description": "Penetrating keratoplasty, right eye", "special_needs": "Corneal tissue, trephine"},
            {"name": "Vitrectomy", "cpt": "67036", "id": "OPHT004", "description": "Pars plana vitrectomy, left eye", "special_needs": "Vitrectomy machine, endolaser"},
        ],
    },
}

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
AIP|1||9941778^{surgeonLastName}^{surgeonFirstName}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|2||99225747^{circulatorLastName}^{circulatorFirstName}^E^^^^^EPIC^^^^PROVID|4.20^Circulator||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|3||99252693^{scrubLastName}^{scrubFirstName}^L^^^^^^EPIC^^^^PROVID|4.150^Scrub||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|4||99252694^{crnaLastName}^{crnaFirstName}^L^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|5||99252695^{anesthesiologistLastName}^{anesthesiologistFirstName}^L^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
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
        tk.Button(self.button_frame, text="Save and Exit", command=self.save_and_exit, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)

        # Base prompts frame
        self.base_prompts_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.base_prompts_frame.pack(fill=tk.X, pady=5)
        self.base_entries = {}
        self.setup_base_prompts()

        # Staff frame
        self.staff_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.staff_frame.pack(fill=tk.X, pady=5)
        self.setup_staff_fields()

        # Additional staff members frame
        self.staff_members_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.staff_members_frame.pack(fill=tk.X, pady=5)

        # Procedures frame
        self.procedures_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        self.procedures_frame.pack(fill=tk.X, pady=5)

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

        # Expand/Collapse buttons
        tree_button_frame = tk.Frame(self.procedure_frame, bg=BG_COLOR)
        tree_button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(tree_button_frame, text="Expand", command=self.expand_tree, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)
        tk.Button(tree_button_frame, text="Collapse", command=self.collapse_tree, bg=BG_COLOR, fg=TEXT_COLOR, activebackground="#3A3C5A").pack(side=tk.LEFT, padx=5)

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

    def expand_tree(self):
        """Expand all Treeview nodes."""
        def expand_node(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_node(child)
        for item in self.tree.get_children():
            expand_node(item)

    def collapse_tree(self):
        """Collapse all Treeview nodes."""
        def collapse_node(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_node(child)
        for item in self.tree.get_children():
            collapse_node(item)

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
                    if patient["procedures"]:
                        proc = patient["procedures"][-1]
                        proc["{procedure}"].set(proc_name)
                        proc["{procedureId}"].set(proc_id)
                        proc["{procedureDescription}"].set(proc_desc)
                        proc["{specialNeeds}"].set(proc_needs)
                        proc["{cptCode}"].set(proc_cpt)
                    else:
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
            if patient["procedures"]:
                target_proc = patient["procedures"][-1]
                target_proc["{procedure}"].set(proc["name"])
                target_proc["{procedureId}"].set(proc["id"])
                target_proc["{procedureDescription}"].set(proc["description"])
                target_proc["{specialNeeds}"].set(proc["special_needs"])
                target_proc["{cptCode}"].set(proc["cpt"])
            else:
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
            self.procedure_frame.configure(width=250)
            self.procedure_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
            self.procedure_panel_visible = True

    def setup_staff_fields(self):
        """Set up fixed staff fields for Surgeon, Circulator, Scrub, CRNA, Anesthesiologist."""
        roles = ["Surgeon", "Circulator", "Scrub", "ANE CRNA", "Anesthesiologist"]
        self.staff_vars = []
        for role in roles:
            frame = tk.Frame(self.staff_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=role, fg=TEXT_COLOR, bg=BG_COLOR, width=15, anchor="w").pack(side=tk.LEFT, padx=5)
            last_name_var = tk.StringVar()
            first_name_var = tk.StringVar()
            tk.Label(frame, text="Last Name:", fg=TEXT_COLOR, bg=BG_COLOR, width=12, anchor="w").pack(side=tk.LEFT, padx=2)
            last_entry = UppercaseEntry(frame, textvariable=last_name_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=20)
            last_entry.pack(side=tk.LEFT, padx=5)
            tk.Label(frame, text="First Name:", fg=TEXT_COLOR, bg=BG_COLOR, width=12, anchor="w").pack(side=tk.LEFT, padx=2)
            first_entry = UppercaseEntry(frame, textvariable=first_name_var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, width=20)
            first_entry.pack(side=tk.LEFT, padx=5)
            last_name_var.trace_add("write", lambda *args: self.update_preview())
            first_name_var.trace_add("write", lambda *args: self.update_preview())
            self.staff_vars.append({"role": role, "lastName": last_name_var, "firstName": first_name_var})

    def setup_base_prompts(self):
        """Set up base prompts with entry fields."""
        for prompt in base_prompts:
            frame = tk.Frame(self.base_prompts_frame, bg=BG_COLOR)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=prompt['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, width=50, anchor="w").pack(side=tk.LEFT, padx=5)
            var = tk.StringVar()
            entry = UppercaseEntry(frame, textvariable=var, bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.base_entries[prompt['key']] = entry
            var.trace_add("write", lambda *args: self.update_preview())

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
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, width=50, anchor="w").pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, textvariable=staff[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            staff[field['key']].trace_add("write", lambda *args: self.update_preview())

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
            'staff_members': [],
            'fixed_staff': [
                {"role": "Surgeon", "lastName": tk.StringVar(), "firstName": tk.StringVar()},
                {"role": "Circulator", "lastName": tk.StringVar(), "firstName": tk.StringVar()},
                {"role": "Scrub", "lastName": tk.StringVar(), "firstName": tk.StringVar()},
                {"role": "ANE CRNA", "lastName": tk.StringVar(), "firstName": tk.StringVar()},
                {"role": "Anesthesiologist", "lastName": tk.StringVar(), "firstName": tk.StringVar()}
            ],
            'messages': []
        }
        self.patients.append(patient)
        self.current_patient_index = len(self.patients) - 1
        self.load_patient()

    def load_patient(self):
        """Load the current patient's data into the GUI."""
        patient = self.patients[self.current_patient_index]
        for key, entry in self.base_entries.items():
            var = patient['base_vars'][key]
            entry.config(textvariable=var)
        for i, staff in enumerate(self.staff_vars):
            patient_staff = patient['fixed_staff'][i]
            staff["lastName"].set(patient_staff["lastName"].get())
            staff["firstName"].set(patient_staff["firstName"].get())
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
            tk.Label(subframe, text=field['prompt'], fg=TEXT_COLOR, bg=BG_COLOR, width=50, anchor="w").pack(side=tk.LEFT, padx=5)
            entry = UppercaseEntry(subframe, textvariable=proc[field['key']], bg=PREVIEW_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
            entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            proc[field['key']].trace_add("write", lambda *args: self.update_preview())

    def update_preview(self):
        """Update the preview with the current patient's S12 message."""
        if 0 <= self.current_patient_index < len(self.patients):
            patient = self.patients[self.current_patient_index]
            template = self.build_template(patient)
            s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
            base_values = {k: v.get() for k, v in patient['base_vars'].items() if v.get()}
            for staff in patient['fixed_staff']:
                role_key = staff['role'].lower().replace(" ", "") + "LastName"
                first_key = staff['role'].lower().replace(" ", "") + "FirstName"
                base_values[role_key] = staff['lastName'].get() or "{lastName}"
                base_values[first_key] = staff['firstName'].get() or "{firstName}"
            for staff in patient['staff_members']:
                role_key = staff['role'].get().lower().replace(" ", "") + "LastName"
                first_key = staff['role'].get().lower().replace(" ", "") + "FirstName"
                base_values[role_key] = staff['lastName'].get() or "{lastName}"
                base_values[first_key] = staff['firstName'].get() or "{firstName}"
            preview_text = s12_template
            for key, val in base_values.items():
                preview_text = preview_text.replace("{" + key + "}", val)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, preview_text)

    def build_template(self, patient):
        """Build the HL7 template."""
        template = default_hl7
        procedures = patient['procedures']
        staff_members = patient['staff_members']
        for i, proc in enumerate(procedures, start=2):
            proc_values = {k: v.get() for k, v in proc.items() if v.get()}
            template = self.duplicate_procedure_segments(template, i, proc_values)
        for i, staff in enumerate(staff_members, start=6):  # Start after fixed staff (AIP 1-5)
            staff_values = {k: v.get() for k, v in staff.items() if v.get()}
            template = self.add_staff_segment(template, staff_values, i)
        return template

    def duplicate_procedure_segments(self, template, proc_num, proc_values):
        """Duplicate AIS through AIP segments."""
        lines = template.splitlines()
        start_idx = next(i for i, line in enumerate(lines) if line.startswith("AIS|1|"))
        end_idx = next(i for i, line in enumerate(lines) if line.startswith("AIP|5|")) + 1
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

    def add_staff_segment(self, template, staff_values, aip_num):
        """Append a new AIP segment."""
        lines = template.splitlines()
        role = staff_values.get("role", "Staff")
        last_name = staff_values.get("lastName", "{lastName}")
        first_name = staff_values.get("firstName", "{firstName}")
        new_aip = f"AIP|{aip_num}||99252695^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|{role}||{{YYYYMMDD}}{{scheduledTime}}|0|S|{{duration}}|S"
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
            template = template.replace("{" + key + "}", val)
        return template

    def build_event_messages(self, template, base_values, duration_min):
        """Generate all 15 HL7 messages."""
        base_date = base_values.get("{YYYYMMDD}", "{YYYYMMDD}")
        setup_time = base_values.get("{scheduledTime}", "{scheduledTime}")
        if base_date == "{YYYYMMDD}" or setup_time == "{scheduledTime}" or not base_date or not setup_time:
            messages = [(template, "00")]
            for i, (event, _) in enumerate(case_events):
                event_replacements = base_values.copy()
                event_replacements["{caseEvent}"] = event
                event_msg = self.fill_template(template, event_replacements)
                messages.append((event_msg, f"{i+1:02}"))
            return messages
        setup_time_clean = setup_time.replace(":", "")
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
        s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
        s12_time = setup_dt.strftime("%H%M%S")
        s12_replacements = base_values.copy()
        s12_replacements["{eventTime}"] = s12_time
        s12_msg = self.fill_template(s12_template, s12_replacements)
        messages.append((s12_msg, "00"))
        for event, offset in case_events:
            event_time = self.get_event_time(setup_dt, offset, duration_min, event_times)
            event_times[event] = event_time
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
        for staff in patient['fixed_staff']:
            role_key = staff['role'].lower().replace(" ", "") + "LastName"
            first_key = staff['role'].lower().replace(" ", "") + "FirstName"
            base_values[role_key] = staff['lastName'].get() or "{lastName}"
            base_values[first_key] = staff['firstName'].get() or "{firstName}"
        for staff in patient['staff_members']:
            role_key = staff['role'].get().lower().replace(" ", "") + "LastName"
            first_key = staff['role'].get().lower().replace(" ", "") + "FirstName"
            base_values[role_key] = staff['lastName'].get() or "{lastName}"
            base_values[first_key] = staff['firstName'].get() or "{firstName}"
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
    {"key": "{procedureId}", "prompt": "Enter Procedure ID"},
    {"key": "{cptCode}", "prompt": "Enter CPT"},
]

procedure_fields = [
    {"key": "{procedure}", "prompt": "What's the procedure name?"},
    {"key": "{procedureDescription}", "prompt": "What's the procedure description?"},
    {"key": "{specialNeeds}", "prompt": "Does this procedure have any special needs?"},
    {"key": "{locationDepartment}", "prompt": "What department should this procedure be scheduled for?"},
    {"key": "{locationOR}", "prompt": "What OR room should this procedure be scheduled for?"},
    {"key": "{procedureId}", "prompt": "Enter Procedure ID"},
    {"key": "{cptCode}", "prompt": "Enter CPT"},
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