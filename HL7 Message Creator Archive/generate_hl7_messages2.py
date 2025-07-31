import os
from datetime import datetime, timedelta

def get_input(prompt, default=None, required=False):
    while True:
        value = input(prompt)
        if value.strip():
            return value.strip()
        elif not required:
            return default
        else:
            print("This field is required. Please enter a value.")

# ==== User Inputs ====
first_name = get_input("What's the patient's first name? (default: {{patientFirstName}}): ", "{patientFirstName}")
last_name = get_input("What's the patient's last name? (default: {{patientLastName}}): ", "{patientLastName}")
procedure = get_input("What is the procedure to be scheduled? (default: {{procedure}}): ", "{procedure}")
case_id = get_input("Would you like to specify the case ID (MRN)? (default: {{caseID}}): ", "{caseID}")
location_id = get_input("Enter location ID (default: {{locationID}}): ", "{locationID}")
description = get_input("What is the procedure description (Special Needs)? (optional): ", "")  # 👈 Add this here

# ==== Required Case Start Time ====
while True:
    start_time_input = input("What time should the case event 'setup' start? (HH:MM, 24hr format): ").strip()
    try:
        setup_time = datetime.strptime(start_time_input, "%H:%M")
        surgery_datetime = datetime.now().replace(hour=setup_time.hour, minute=setup_time.minute, second=0, microsecond=0)
        break
    except ValueError:
        print("⚠️ Invalid time format. Please use HH:MM in 24hr format.")

# ==== Case Duration ====
duration_input = get_input("How long is the duration of the case (in minutes)? (default: 120): ", "120")
try:
    duration_minutes = int(duration_input)
except ValueError:
    duration_minutes = 120

# ==== Event Time Offsets ====
events = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -5),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", duration_minutes - 30),
    ("complete", duration_minutes - 15),
    ("exiting", duration_minutes - 10),
    ("ordered_pacu", duration_minutes - 5),
    ("planned_pacu", 0),
    ("in_pacu", 5),
    ("out_pacu", 90),
]

# ==== HL7 Template ====
hl7_template = """
MSH|^~\\&|EPIC|NC||NC|{timestamp}||SIU^S12|{case_id}|P|2.5
SCH||{case_id}|||||||{duration}|S|^^^{setup_datetime}
ZCS|{event}|Y|ORSCH_S12||||49000^PR EXPLORATORY OF ABDOMEN^CPT
PID|1||{case_id}^^^MRN^MRN||{patientLastName}^{patientFirstName}||19740912|F|{patientFirstName}^{patientLastName}^^|||||||||380207923
PV1||Emergency|NC-PERIOP^^^NC|||||||GEN|||||||||{case_id}
RGS|
{obx_block}AIS|1||2753^{procedure}|{event_time}|0|S|4500|S||||2
{nte_block}
AIL|1||^{location_id}^^AIPOR
AIP|1||9941778^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{setup_time}|0|S|{duration}|S
AIP|2||99225747^SMITH^JANE^ELIZABETH^^^^^EPIC^^^^PROVID|4.20^Circulator||{setup_time}|0|S|{duration}|S
AIP|3||99252693^CLARK^LISA^L^^^^^^EPIC^^^^PROVID|4.150^Scrub ||{setup_time}|0|S|{duration}|S
AIP|4|||2.20^ANE CRNA||{setup_time}|0|S|{duration}|S
AIP|5|||2.139^Anesthesiologist||{setup_time}|0|S|{duration}|S
"""

# ==== File Output ====
location_id = get_input("Enter location ID (default: {locationID}): ", "{locationID}")
output_dir = f"CurrentDay/Patient_{case_id}"
os.makedirs(output_dir, exist_ok=True)

# ==== Write HL7 Files ====
for i, (event, offset) in enumerate(events, start=1):
    event_time = surgery_datetime + timedelta(minutes=offset)
    event_time_str = event_time.strftime("%Y%m%d%H%M")
    timestamp = event_time.strftime("%Y%m%d%H%M%S")
    setup_str = surgery_datetime.strftime("%Y%m%d%H%M")
    event_date = event_time.strftime("%Y%m%d")

    nte_block = f"NTE|1||{description}|Procedure Description|||" if description else ""

    # OBX block (exclude for the very first message)
    if i == 1:
        obx_block = ""
    else:
        obx_block = f"OBX|1|DTM|{event}|In|{event_date}{event_time.strftime('%H%M')}|||||||||{event_date}{event_time.strftime('%H%M')}||||||||||||||||||"

message = hl7_template.format(
    timestamp=timestamp,
    case_id=case_id,
    first_name=first_name,
    last_name=last_name,
    procedure=procedure,
    event=event,
    event_time=event_time_str,
    setup_time=setup_str,
    setup_datetime=setup_str,
    nte_block=nte_block,
    location_id=location_id,
    obx_block=obx_block,
    duration=duration_minutes
)

filename = f"{i:02d}_{event.upper()}.hl7"
with open(os.path.join(output_dir, filename), "w") as f:
        f.write(message)

print(f"✅ Created {filename}")

print(f"\n🎉 HL7 messages saved to: {output_dir}")
