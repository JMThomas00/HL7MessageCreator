import os
import random
from datetime import datetime, timedelta

# Default HL7 template
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

# List of case events and relative timing (in minutes)
case_events = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -5),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", "duration-30"),
    ("complete", "duration-15"),
    ("exiting", "duration-10"),
    ("ordered_pacu", "duration-5"),
    ("planned_pacu", 0),
    ("in_pacu", 5),
    ("out_pacu", 90),
]

def prompt_user(template: str):
    print("\nLeave a field blank if it should remain unchanged\n")

    prompts = {
        "{patientLastName}": "What's the patient's last name?",
        "{patientFirstName}": "What's the patient's first name?",
        "{patientMRN}": "Enter a new MRN for the patient?",
        "{YYYYMMDD}": "Schedule the date of the procedure? (Format is YYYYMMDD)?",
        "{scheduledTime}": "What's the setup time of the procedure? (Format is HH:MM)?",
        "{duration}": "How long is the case scheduled for? Leave blank for random (60-120 min):",
        "{procedure}": "What's the procedure name?",
        "{procedureDescription}": "What's the procedure description?",
        "{specialNeeds}": "Does this case have any special needs?",
        "{locationDepartment}": "What department should this be scheduled for?",
        "{locationOR}": "What OR room should this be scheduled for?"
    }

    values = {}
    for key, prompt in prompts.items():
        val = input(f"{prompt} ").strip()
        if val:
            values[key] = val

    # Auto-generate duration if not provided
    if "{duration}" not in values:
        values["{duration}"] = str(random.randint(60, 120))

    return values

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

def build_event_messages(template, values, duration_min):
    base_date = values.get("{YYYYMMDD}")
    setup_time = values.get("{scheduledTime}")
    setup_dt = datetime.strptime(f"{base_date} {setup_time}", "%Y%m%d %H:%M")
        
    messages = []
    event_num = 0

    # Initial S12 message (no OBX segment)
    s12_msg = fill_template(template, values).splitlines()
    s12_msg = [line for line in s12_msg if not line.startswith("OBX")]
    messages.append(("\n".join(s12_msg), "00"))

    for i, (event, offset) in enumerate(case_events):
        event_time = get_event_time(setup_dt, offset, duration_min)
        time_str = event_time.strftime("%H%M")
        date_str = event_time.strftime("%Y%m%d")
        event_replacements = values.copy()
        event_replacements["{eventTime}"] = time_str
        event_replacements["{caseEvent}"] = event
        event_replacements["{YYYYMMDD}"] = date_str
        event_replacements["{scheduledTime}"] = setup_dt.strftime("%H%M")

        msg = fill_template(template, event_replacements)
        messages.append((msg, f"{i+1:02}"))  # Event file index starts at 01
    
    return messages

def main():
    use_existing = input("Would you like to import an existing HL7 message? (y/n): ").lower()
    if use_existing == 'y':
        path = input("Enter the path to the HL7 message: ").strip()
        try:
            with open(path, 'r') as f:
                hl7_template = f.read()
            print("\nImported HL7 Message:\n")
            print(hl7_template)
        except FileNotFoundError:
            print("File not found. Using default template.")
            hl7_template = default_hl7
    else:
        hl7_template = default_hl7

    patient_done = False
    all_messages = []

    while not patient_done:
        values = prompt_user(hl7_template)
        duration_min = int(values["{duration}"])
        messages = build_event_messages(hl7_template, values, duration_min)
        all_messages.extend(messages)

        multi = input("Is this a multi-procedure case? Add another procedure? (y/n): ").lower()
        if multi != 'y':
            patient_done = True

    # Output messages to files
    out_dir = f"{datetime.now():%y%m%d} - HL7 Output"
    os.makedirs(out_dir, exist_ok=True)

    base_name = f"{values.get('{patientFirstName}', 'First')}{values.get('{patientLastName}', 'Last')}"
    for msg, idx in all_messages:
        filename = f"{base_name}-{idx}.hl7"
        with open(os.path.join(out_dir, filename), 'w') as f:
            f.write(msg)

    print(f"\nHL7 messages written to '{out_dir}'")

if __name__ == "__main__":
    main()
