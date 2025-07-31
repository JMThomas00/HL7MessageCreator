import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import os
import random
from datetime import datetime, timedelta

# Default HL7 template (same as provided)
default_hl7 = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||SIU^S12|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|S|^^^{YYYYMMDD}{scheduledTime}
ZCS|{caseEvent}|Y|ORSCH_S14||||49000^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||19740912|F|{patientLastName}^{patientFirstName}^^|||||||||380207923
PV1||Emergency|NC-PERIOP^^^NC|||||||GEN|||||||||{patientMRN}
RGS|
OBX|1|DTM|{caseEvent}|In|{YYYYMMDD}{eventTime}|||||||||{YYYYMMDD}{eventTime}||||||||||||||||||
AIS|1||{procedureId}^{procedure}|{YYYYMMDD}{scheduledTime}|0|S|4500|S||||2
NTE|1||{procedureDescription}|Procedure Description|||
NTE|2||{specialNeeds}|CaseNotes|||
AIL|1||^{locationOR}^^{locationDepartment}
AIP|1||9941778^{primaryLastName}^{primaryFirstName}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|2||99225747^{lastName}^{firstName}^E^^^^^EPIC^^^^PROVID|4.20^Circulator||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|3||99252693^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|4.150^Scrub ||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|4||99252694^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
AIP|5||99252695^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{YYYYMMDD}{scheduledTime}|0|S|{duration}|S
"""

# Case events (same as provided)
case_events = [
    ("arrive", -60), ("in_preop", -45), ("out_preop", -15), ("planned_preop", -5),
    ("setup", 0), ("intraop", 10), ("started", 15), ("closing", "duration-30"),
    ("complete", "duration-15"), ("exiting", "duration-10"), ("ordered_pacu", "duration-5"),
    ("planned_pacu", 0), ("in_pacu", 5), ("out_pacu", 90),
]

# List to store procedure dictionaries
procedures = []

# Functions from original script (unchanged except for integration)
def duplicate_procedure_segments(template, proc_num, proc_values):
    lines = template.splitlines()
    start_idx = next(i for i, line in enumerate(lines) if line.startswith("AIS|1|"))
    end_idx = next(i for i, line in enumerate(lines) if line.startswith("AIP|5|")) + 1
    proc_block = lines[start_idx:end_idx]
    
    new_block = []
    nte_count = 2 * (proc_num - 1)
    aip_count = 5 * (proc_num - 1)
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
        elif line.startswith("AIP|"):
            aip_count += 1
            parts = line.split("|")
            parts[1] = str(aip_count)
            new_line = "|".join(parts)
        else:
            new_line = line
        for key, val in proc_values.items():
            new_line = new_line.replace(key, val)
        new_block.append(new_line)
    
    insert_idx = end_idx + (end_idx - start_idx) * (proc_num - 2)
    lines[insert_idx:insert_idx] = new_block
    return "\n".join(lines)

def get_event_time(base_time, offset, duration):
    if isinstance(offset, str) and offset.startswith("duration"):
        delta = int(offset.split("-")[1])
        minutes = duration - delta
    else:
        minutes = offset
    return base_time + timedelta(minutes=minutes + random.randint(-2, 2))

def fill_template(template, replacements):
    for key, val in replacements.items():
        template = template.replace(key, val)
    return template

def build_event_messages(template, base_values, duration_min):
    base_date = base_values["{YYYYMMDD}"]
    setup_time = base_values["{scheduledTime}"]
    setup_dt = datetime.strptime(f"{base_date} {setup_time}", "%Y%m%d %H%M")
    
    messages = []
    s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
    s12_time = setup_dt.strftime("%H%M")
    s12_replacements = base_values.copy()
    s12_replacements["{eventTime}"] = s12_time
    s12_msg = fill_template(s12_template, s12_replacements)
    messages.append((s12_msg, "00"))
    
    for i, (event, offset) in enumerate(case_events):
        event_time = get_event_time(setup_dt, offset, duration_min)
        time_str = event_time.strftime("%H%M")
        date_str = event_time.strftime("%Y%m%d")
        event_replacements = base_values.copy()
        event_replacements["{eventTime}"] = time_str
        event_replacements["{caseEvent}"] = event
        event_replacements["{YYYYMMDD}"] = date_str
        event_msg = fill_template(template, event_replacements)
        messages.append((event_msg, f"{i+1:02}"))
    
    return messages

# GUI Functions
def select_template_file():
    file_path = filedialog.askopenfilename(filetypes=[("HL7 Files", "*.hl7"), ("All Files", "*.*")])
    if file_path:
        try:
            with open(file_path, 'r') as f:
                global template_text
                template_text = f.read()
            template_label.config(text=f"Template: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")

def update_template_selection(*args):
    global template_text
    if template_var.get() == 0:
        template_text = default_hl7
        template_label.config(text="Template: default")
        select_file_button.config(state='disabled')
    else:
        select_file_button.config(state='normal')

def update_duration_entry(*args):
    if random_duration_var.get():
        duration_label.grid_remove()
        duration_entry.grid_remove()
    else:
        duration_label.grid()
        duration_entry.grid()

def add_procedure():
    duration = str(random.randint(60, 120)) if random_duration_var.get() else (duration_entry.get() or "0")
    proc_values = {
        "{procedure}": procedure_name_entry.get(),
        "{procedureDescription}": procedure_desc_entry.get(),
        "{specialNeeds}": special_needs_entry.get(),
        "{locationDepartment}": location_dept_entry.get(),
        "{locationOR}": location_or_entry.get(),
        "{procedureId}": procedure_id_entry.get() or "49000",
        "{primaryLastName}": surgeon_last_entry.get(),
        "{primaryFirstName}": surgeon_first_entry.get(),
        "{duration}": duration
    }
    procedures.append(proc_values)
    
    # Clear fields
    procedure_name_entry.delete(0, tk.END)
    procedure_desc_entry.delete(0, tk.END)
    special_needs_entry.delete(0, tk.END)
    location_dept_entry.delete(0, tk.END)
    location_or_entry.delete(0, tk.END)
    procedure_id_entry.delete(0, tk.END)
    surgeon_last_entry.delete(0, tk.END)
    surgeon_first_entry.delete(0, tk.END)
    if not random_duration_var.get():
        duration_entry.delete(0, tk.END)
    
    procedure_count_label.config(text=f"Procedures added: {len(procedures)}")

def generate_messages():
    if not procedures:
        messagebox.showerror("Error", "Please add at least one procedure.")
        return
    
    # Collect base values
    patient_last = last_name_entry.get()
    patient_first = first_name_entry.get()
    patient_mrn = mrn_entry.get()
    procedure_date = date_entry.get()
    procedure_time = time_entry.get().replace(":", "")
    
    first_proc = procedures[0]
    total_duration = sum(int(proc["{duration}"]) for proc in procedures)
    base_values = {
        "{patientLastName}": patient_last,
        "{patientFirstName}": patient_first,
        "{patientMRN}": patient_mrn,
        "{YYYYMMDD}": procedure_date,
        "{scheduledTime}": procedure_time,
        "{procedure}": first_proc["{procedure}"],
        "{procedureDescription}": first_proc["{procedureDescription}"],
        "{specialNeeds}": first_proc["{specialNeeds}"],
        "{locationDepartment}": first_proc["{locationDepartment}"],
        "{locationOR}": first_proc["{locationOR}"],
        "{procedureId}": first_proc["{procedureId}"],
        "{primaryLastName}": first_proc["{primaryLastName}"],
        "{primaryFirstName}": first_proc["{primaryFirstName}"],
        "{duration}": str(total_duration)
    }
    
    # Build full template with additional procedures
    full_template = template_text
    for proc_num in range(1, len(procedures)):
        proc_values = procedures[proc_num]
        full_template = duplicate_procedure_segments(full_template, proc_num + 1, proc_values)
    
    # Generate messages
    duration_min = int(base_values["{duration}"])
    messages = build_event_messages(full_template, base_values, duration_min)
    
    # Output to files
    out_dir = f"{datetime.now():%y%m%d} - HL7 Output"
    os.makedirs(out_dir, exist_ok=True)
    base_name = f"{base_values.get('{patientFirstName}', 'First')}{base_values.get('{patientLastName}', 'Last')}"
    for msg, idx in messages:
        filename = f"{base_name}-{idx}.hl7"
        with open(os.path.join(out_dir, filename), 'w') as f:
            f.write(msg)
    messagebox.showinfo("Success", f"HL7 messages written to '{out_dir}'")

# Set up GUI
root = tk.Tk()
root.title("HL7 Message Generator")
root.configure(background='#1f2139')

# Apply dark theme
style = ttk.Style()
style.theme_use('clam')
style.configure('TFrame', background='#1f2139')
style.configure('TLabel', background='#1f2139', foreground='#ffffff')
style.configure('TEntry', fieldbackground='#2e2e2e', foreground='#ffffff', insertbackground='#ffffff', selectbackground='#7dcae3')
style.configure('TButton', background='#465be7', foreground='#ffffff')
style.configure('TRadiobutton', background='#1f2139', foreground='#ffffff')
style.configure('TCheckbutton', background='#1f2139', foreground='#ffffff')

# Template Selection
template_text = default_hl7
template_frame = ttk.LabelFrame(root, text="Template Selection", padding=10)
template_frame.pack(pady=10, fill='x')
template_var = tk.IntVar(value=0)
ttk.Radiobutton(template_frame, text="Use default template", variable=template_var, value=0).pack(side='left', padx=5)
ttk.Radiobutton(template_frame, text="Import from file", variable=template_var, value=1).pack(side='left', padx=5)
select_file_button = ttk.Button(template_frame, text="Select File", command=select_template_file, state='disabled')
select_file_button.pack(side='left', padx=5)
template_label = ttk.Label(template_frame, text="Template: default")
template_label.pack(side='left', padx=5)
template_var.trace('w', update_template_selection)
update_template_selection()

# Patient Information
patient_frame = ttk.LabelFrame(root, text="Patient Information", padding=10)
patient_frame.pack(pady=10, fill='x')
ttk.Label(patient_frame, text="Last Name:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
last_name_entry = ttk.Entry(patient_frame)
last_name_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
ttk.Label(patient_frame, text="First Name:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
first_name_entry = ttk.Entry(patient_frame)
first_name_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
ttk.Label(patient_frame, text="MRN:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
mrn_entry = ttk.Entry(patient_frame)
mrn_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

# Procedure Date and Time
date_time_frame = ttk.LabelFrame(root, text="Procedure Date and Time", padding=10)
date_time_frame.pack(pady=10, fill='x')
ttk.Label(date_time_frame, text="Date (YYYYMMDD):").grid(row=0, column=0, sticky='e', padx=5, pady=5)
date_entry = ttk.Entry(date_time_frame)
date_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
ttk.Label(date_time_frame, text="Time (HH:MM):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
time_entry = ttk.Entry(date_time_frame)
time_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

# Procedure Details
procedure_frame = ttk.LabelFrame(root, text="Procedure Details", padding=10)
procedure_frame.pack(pady=10, fill='x')
fields = [
    ("Procedure Name:", "procedure_name_entry"),
    ("Procedure Description:", "procedure_desc_entry"),
    ("Special Needs:", "special_needs_entry"),
    ("Location Department:", "location_dept_entry"),
    ("Location OR:", "location_or_entry"),
    ("Procedure ID (default 49000):", "procedure_id_entry"),
    ("Surgeon Last Name:", "surgeon_last_entry"),
    ("Surgeon First Name:", "surgeon_first_entry"),
]
for i, (label, var_name) in enumerate(fields):
    ttk.Label(procedure_frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=5)
    entry = ttk.Entry(procedure_frame)
    entry.grid(row=i, column=1, sticky='w', padx=5, pady=5)
    globals()[var_name] = entry

# Duration handling
random_duration_var = tk.BooleanVar(value=True)
duration_check = ttk.Checkbutton(procedure_frame, text="Use random duration (60-120 min)", variable=random_duration_var)
duration_check.grid(row=8, column=0, columnspan=2, sticky='w', padx=5, pady=5)
duration_label = ttk.Label(procedure_frame, text="Duration (min):")
duration_label.grid(row=9, column=0, sticky='e', padx=5, pady=5)
duration_entry = ttk.Entry(procedure_frame)
duration_entry.grid(row=9, column=1, sticky='w', padx=5, pady=5)
random_duration_var.trace('w', update_duration_entry)
update_duration_entry()

# Add Procedure Button and Counter
add_procedure_button = ttk.Button(procedure_frame, text="Add Procedure", command=add_procedure)
add_procedure_button.grid(row=10, column=0, columnspan=2, pady=10)
procedure_count_label = ttk.Label(procedure_frame, text="Procedures added: 0")
procedure_count_label.grid(row=11, column=0, columnspan=2)

# Generate Messages Button
generate_button = ttk.Button(root, text="Generate Messages", command=generate_messages)
generate_button.pack(pady=20)

# Start the GUI
root.mainloop()