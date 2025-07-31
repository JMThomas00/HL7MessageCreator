import os
import random
from datetime import datetime, timedelta

# Constants
CASE_EVENTS = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -5),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", "duration - 30"),
    ("complete", "duration - 15"),
    ("exiting", "duration - 10"),
    ("ordered_pacu", "duration - 5"),
    ("planned_pacu", 0),
    ("in_pacu", 5),
    ("out_pacu", 90),
]

TEMPLATE_PATH = "hl7_template.hl7"

def prompt_variable(prompt, default_placeholder):
    response = input(f"{prompt} (Default is no): y/n? ").strip().lower()
    if response == "y":
        return input(f"Enter new value for {default_placeholder}: ").strip()
    return f"{{{default_placeholder}}}"

def generate_random_duration():
    return random.randint(90, 180)

def apply_time_variation(base_time, offset):
    variation = timedelta(minutes=random.randint(-15, 15))
    return base_time + timedelta(minutes=offset) + variation

def format_time(dt):
    return dt.strftime("%y%m%d%H%M")

def create_event_hl7(event_name, event_time, patient_info, procedure_info, duration, is_s12=False):
    obx_segment = ""
    if not is_s12:
        obx_segment = f"OBX|1|DTM|{event_name}|In|{event_time}|||||||||{event_time}||||||||||||||||||\n"

    multi_proc_segments = ""
    for idx, proc in enumerate(procedure_info):
        proc_idx = idx + 1
        multi_proc_segments += f"AIS|{proc_idx}||{proc['procedureId']}^{proc['procedure']}|{patient_info['scheduled_datetime']}|0|S|4500|S||||2\n"
        multi_proc_segments += f"NTE|1||{proc['procedureDescription']}|Procedure Description|||\n"
        if proc['specialNeeds']:
            multi_proc_segments += f"NTE|2||{proc['specialNeeds']}|specialneeds|||\n"

    event_type = "ORSCH_S12" if is_s12 else "ORSCH_S14"
    hl7 = f"""
MSH|^~\&|EPIC|NC||NC|{patient_info['schedule_date']}000000||SIU^{'S12' if is_s12 else 'S14'}|{patient_info['patientMRN']}|P|2.5
SCH||{patient_info['patientMRN']}|||||||{duration}|S|^^^{patient_info['scheduled_datetime']}
ZCS|{event_name}|Y|{event_type}||||49000^{procedure_info[0]['procedure']}^CPT
PID|1||{patient_info['patientMRN']}^^^MRN^MRN||{patient_info['patientLastName']}^{patient_info['patientFirstName']}||19740912|F|{patient_info['patientLastName']}^{patient_info['patientFirstName']}^^|||||||||380207923
PV1||Emergency|NC-PERIOP^^^NC|||||||GEN|||||||||{patient_info['patientMRN']}
RGS|
{obx_segment}{multi_proc_segments}AIL|1||^{patient_info['locationOR']}^^{patient_info['locationDepartment']}
AIP|1||9941778^lastname^firstname^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{patient_info['scheduled_datetime']}|0|S|{duration}|S
AIP|2||99225747^lastname^firstname^E^^^^^EPIC^^^^PROVID|4.20^Circulator||{patient_info['scheduled_datetime']}|0|S|{duration}|S
AIP|3||99252693^lastname^firstname^L^^^^^^EPIC^^^^PROVID|4.150^Scrub ||{patient_info['scheduled_datetime']}|0|S|{duration}|S
AIP|4||99252694^lastname^firstname^L^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{patient_info['scheduled_datetime']}|0|S|{duration}|S
AIP|5||99252695^lastname^firstname^L^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{patient_info['scheduled_datetime']}|0|S|{duration}|S
"""
    return hl7.strip()

# Main Script
now = datetime.now()
out_dir = now.strftime("%y%m%d") + " - HL7 Output"
os.makedirs(out_dir, exist_ok=True)

# Prompt for patient and procedure info
schedule_date_input = prompt_variable("Schedule the date of the procedure? (Format is YYMMDD)", "schedule_date")
scheduled_time_input = input("What's the setup time of the procedure? (Format is HH:MM): ").strip() or "{scheduledTime}"

try:
    schedule_datetime = datetime.strptime(schedule_date_input + scheduled_time_input, "%y%m%d%H:%M")
    formatted_schedule_date = schedule_date_input
    formatted_schedule_datetime = schedule_datetime.strftime("%y%m%d%H%M")
except:
    schedule_datetime = now
    formatted_schedule_date = schedule_date_input
    formatted_schedule_datetime = "{scheduledDatetime}"

patient_info = {
    "patientLastName": input("What's the patient's last name? ").strip() or "{patientLastName}",
    "patientFirstName": input("What's the patient's first name? ").strip() or "{patientFirstName}",
    "patientMRN": prompt_variable("Change the patient's MRN?", "patientMRN"),
    "schedule_date": formatted_schedule_date,
    "scheduled_time": scheduled_time_input,
    "locationDepartment": input("What department should this be scheduled for? ").strip() or "{locationDepartment}",
    "locationOR": input("What OR room should this be scheduled for? ").strip() or "{locationOR}",
    "scheduled_datetime": formatted_schedule_datetime
}

procedure_info = []

# At least one procedure
while True:
    proc = {
        "procedure": input("What's the procedure name? ").strip() or "{procedure}",
        "procedureDescription": input("What's the procedure description? ").strip() or "{procedureDescription}",
        "specialNeeds": input("Are there any special needs for this procedure? If yes, enter it now otherwise leave blank: ").strip(),
        "procedureId": str(random.randint(1000, 9999))
    }
    procedure_info.append(proc)
    more = input("Is this a multi-procedure case? Would you like to schedule an additional case for this patient? y/n: ").strip().lower()
    if more != 'y':
        break

# Generate duration
duration = generate_random_duration()

# Generate initial S12 scheduling message
initial_hl7 = create_event_hl7("scheduled", patient_info["scheduled_datetime"], patient_info, procedure_info, duration, is_s12=True)
filename = f"{patient_info['patientFirstName']}{patient_info['patientLastName']}-00.hl7"
with open(os.path.join(out_dir, filename), 'w') as f:
    f.write(initial_hl7)

# Generate each HL7 message for case events
for idx, (event_name, offset) in enumerate(CASE_EVENTS):
    if isinstance(offset, str) and "duration" in offset:
        mins = duration - int(offset.split('-')[-1].strip())
        event_time = apply_time_variation(schedule_datetime, mins)
    else:
        event_time = apply_time_variation(schedule_datetime, offset)

    event_time_str = format_time(event_time)
    hl7_message = create_event_hl7(event_name, event_time_str, patient_info, procedure_info, duration, is_s12=False)

    filename = f"{patient_info['patientFirstName']}{patient_info['patientLastName']}-{str(idx + 1).zfill(2)}.hl7"
    with open(os.path.join(out_dir, filename), 'w') as f:
        f.write(hl7_message)

print(f"HL7 messages generated in: {out_dir}")