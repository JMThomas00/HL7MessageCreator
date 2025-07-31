import os
import random
from datetime import datetime, timedelta
import argparse

# Default HL7 template
default_hl7 = """
MSH|^~\&|EPIC|NC||NC|{YYYYMMDD}{eventTime}00||SIU^S12|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|S|^^^{YYYYMMDD}{scheduledTime}
ZCS|{caseEvent}|Y|ORSCH_S14||||49000^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||19740912|F|{patientLastName}^{patientFirstName}^^|||||||||380207923
PV1||IP|NC-PERIOP^^^NC|||||||GEN|||||||||{patientMRN}
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

# Case events with relative offsets (in minutes)
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
    ("planned_pacu", "duration+5"),
    ("in_pacu", "duration+5"),
    ("out_pacu", "duration+60"),
]

def load_template():
    """Load HL7 template based on user input."""
    use_existing = input("Would you like to import an existing HL7 message? (y/n): ").lower()
    if use_existing == 'y':
        path = input("Enter the path to the HL7 message: ").strip()
        try:
            with open(path, 'r') as f:
                template = f.read()
            print("\nImported HL7 Message:\n")
            print(template)
            return template
        except FileNotFoundError:
            print("File not found. Using default template.")
    return default_hl7

def prompt_user(args):
    """Prompt user for input values, using command-line args if provided, with defaults."""
    print("\nLeave a field blank if it should remain unchanged\n")
    values = {}

    # Handle date
    if args.date:
        values["{YYYYMMDD}"] = args.date
    else:
        val = input("Schedule the date of the procedure? (Format is YYYYMMDD)? ").strip()
        values["{YYYYMMDD}"] = val if val else "20230101"  # Default to 2023-01-01

    # Handle time
    if args.time:
        values["{scheduledTime}"] = args.time.replace(":", "")
    else:
        val = input("What's the setup time of the procedure? (Format is HH:MM)? ").strip()
        values["{scheduledTime}"] = val.replace(":", "") if val else "0800"  # Default to 08:00

    prompts = {
        "{patientLastName}": "What's the patient's last name?",
        "{patientFirstName}": "What's the patient's first name?",
        "{patientMRN}": "Enter a new MRN for the patient?",
        "{duration}": "How long is the case scheduled for? Leave blank for random (60-120 min):",
        "{procedure}": "What's the procedure name?",
        "{procedureDescription}": "What's the procedure description?",
        "{specialNeeds}": "Does this case have any special needs?",
        "{locationDepartment}": "What department should this be scheduled for?",
        "{locationOR}": "What OR room should this be scheduled for?",
        "{procedureId}": "Enter procedure ID (e.g., CPT code, default 49000 if blank):",
        "{primaryLastName}": "What's the primary surgeon's last name?",
        "{primaryFirstName}": "What's the primary surgeon's first name?"
    }

    for key, prompt in prompts.items():
        val = input(f"{prompt} ").strip()
        if val:
            values[key] = val

    # Handle duration
    if "{duration}" not in values or not values["{duration}"]:
        values["{duration}"] = str(random.randint(60, 120))

    # Handle procedureId
    if "{procedureId}" not in values or not values["{procedureId}"]:
        values["{procedureId}"] = "49000"

    return values

def duplicate_procedure_segments(template, proc_num, proc_values):
    """Duplicate AIS through AIP5 segments for multi-procedure cases."""
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
    """Calculate event time with randomness."""
    if isinstance(offset, str) and offset.startswith("duration"):
        delta = int(offset.split("-")[1])
        minutes = duration - delta
    else:
        minutes = offset
    return base_time + timedelta(minutes=minutes + random.randint(-2, 2))

def fill_template(template, replacements):
    """Fill placeholders in the template."""
    for key, val in replacements.items():
        template = template.replace(key, val)
    return template

def build_event_messages(template, base_values, duration_min):
    """Generate all 15 HL7 messages."""
    base_date = base_values["{YYYYMMDD}"]
    setup_time = base_values["{scheduledTime}"]
    setup_dt = datetime.strptime(f"{base_date} {setup_time}", "%Y%m%d %H%M")
    
    messages = []
    # S12 message (no OBX)
    s12_template = "\n".join(line for line in template.splitlines() if not line.startswith("OBX"))
    s12_time = setup_dt.strftime("%H%M")
    s12_replacements = base_values.copy()
    s12_replacements["{eventTime}"] = s12_time
    s12_msg = fill_template(s12_template, s12_replacements)
    messages.append((s12_msg, "00"))
    
    # Event messages
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

def main():
    """Main function to orchestrate HL7 message generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Procedure date (YYYYMMDD)")
    parser.add_argument("--time", help="Setup time (HH:MM)")
    args = parser.parse_args()

    template = load_template()
    base_values = prompt_user(args)
    duration_min = int(base_values["{duration}"])
    
    # Handle multi-procedure cases
    proc_num = 1
    full_template = template
    while input("Is this a multi-procedure case? Add another procedure? (y/n): ").lower() == 'y':
        proc_num += 1
        print(f"\nEntering details for procedure #{proc_num}")
        proc_values = prompt_user(args)
        full_template = duplicate_procedure_segments(full_template, proc_num, proc_values)
    
    messages = build_event_messages(full_template, base_values, duration_min)
    
    # Output to files
    out_dir = f"{datetime.now():%y%m%d} - HL7 Output"
    os.makedirs(out_dir, exist_ok=True)
    base_name = f"{base_values.get('{patientFirstName}', 'First')}{base_values.get('{patientLastName}', 'Last')}"
    for msg, idx in messages:
        filename = f"{base_name}-{idx}.hl7"
        with open(os.path.join(out_dir, filename), 'w') as f:
            f.write(msg)
    print(f"\nHL7 messages written to '{out_dir}'")

if __name__ == "__main__":
    main()