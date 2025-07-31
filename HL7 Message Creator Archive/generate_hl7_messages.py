import os
from datetime import datetime, timedelta

# ==== User Input ====
first_name = input("Enter patient first name (default: {patientFirstName}): ") or "{patientFirstName}"
last_name = input("Enter patient last name (default: {patientLastName}): ") or "{patientLastName}"
case_id = input("Enter case ID (default: {caseID}): ") or "{caseID}"
location_id = input("Enter location ID (default: {locationID}): ") or "{locationID}"

# ==== Surgery Base Time ====
surgery_date = datetime.now().replace(hour=11, minute=30, second=0, microsecond=0)

# ==== Events & Time Offsets (minutes) ====
events = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -5),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", 90),
    ("complete", 105),
    ("exiting", 110),
    ("ordered_pacu", 115),
    ("planned_pacu", 120),
    ("in_pacu", 125),
    ("out_pacu", 215),
]

# ==== Message Template ====
hl7_template = """MSH|^~\\&|EPIC|NC||NC|{timestamp}||SIU^S12|{case_id}|P|2.5
SCH||{case_id}|||||||8280|S|^^^{surgery_date}
ZCS|{event}|Y|ORSCH_S12||||49000^PR EXPLORATORY OF ABDOMEN^CPT
PID|1||{case_id}^^^MRN^MRN||{last_name}^{first_name}||19740912|F|{first_name}^{last_name}^^|||||||||380207923
PV1||Emergency|NC-PERIOP^^^NC|||||||GEN|||||||||{case_id}
RGS|
AIS|1||2753^LAPAROTOMY, EXPLORATORY|{event_time}|0|S|4500|S||||2
NTE|1||LAPAROTOMY, EXPLORATORY FOR BOWEL RESECTION|Procedure Description|||
AIL|1||^{location_id}^^AIPOR
AIP|1||9941778^{last_name}^{first_name}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{event_time}|0|S|6780|S
AIP|2||99225747^{last_name}^{first_name}^ELIZABETH^^^^^EPIC^^^^PROVID|4.20^Circulator||{event_time}|0|S|8280|S
AIP|3||99252693^{last_name}^{first_name}^L^^^^^^EPIC^^^^PROVID|4.150^Scrub ||{event_time}|0|S|8280|S
AIP|4|||2.20^ANE CRNA||{event_time}|0|S|8280|S
AIP|5|||2.139^Anesthesiologist||{event_time}|0|S|8280|S
"""

# ==== Output Directory ====
output_dir = f"CurrentDay/Patient_{case_id}"
os.makedirs(output_dir, exist_ok=True)

# ==== Generate HL7 Files ====
for i, (event, offset) in enumerate(events, start=1):
    event_time = surgery_date + timedelta(minutes=offset)
    timestamp = event_time.strftime("%Y%m%d%H%M%S")
    surgery_day = surgery_date.strftime("%Y%m%d%H%M")
    event_hl7 = hl7_template.format(
        timestamp=timestamp,
        case_id=case_id,
        first_name=first_name,
        last_name=last_name,
        location_id=location_id,
        event=event,
        surgery_date=surgery_day,
        event_time=event_time.strftime("%Y%m%d%H%M")
    )

    filename = f"{i:02d}_{event.upper()}.hl7"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.write(event_hl7)

    print(f"Generated: {filepath}")

print("\n✅ HL7 messages created in:", output_dir)
