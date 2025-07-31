import os
import random
from datetime import datetime, timedelta

# Template for the HL7 message
HL7_TEMPLATE = """MSH|^~\\&|EPIC|NC||NC|{timestamp}||SIU^S12|{patientMRN}|P|2.5
SCH||{patientMRN}|||||||{duration}|S|^^^{schedule_date}{scheduled_time}
ZCS|{eventName}|Y|ORSCH_S14||||49000^{procedure}^CPT
PID|1||{patientMRN}^^^MRN^MRN||{patientLastName}^{patientFirstName}||19740912|F|{patientLastName}^{patientFirstName}^^|||||||||380207923
PV1||Emergency|NC-PERIOP^^^NC|||||||GEN|||||||||{patientMRN}
RGS|
{obx_block}
{ais_block}
{nte_block}
AIL|1||^{locationOR}^^{locationDepartment}
{aip_block}
"""

# OBX segment
OBX_TEMPLATE = """OBX|1|DTM|{eventName}|In|{event_time}|||||||||{event_time}||||||||||||||||||"""

# AIS, NTE, AIP templates for one procedure
AIS_TEMPLATE = "AIS|{idx}||{procedureId}^{procedure}|{schedule_date}{scheduled_time}|0|S|4500|S||||2"
NTE_TEMPLATE = """NTE|1||{procedureDescription}|Procedure Description|||
NTE|2||{specialNeeds}|specialneeds|||"""

AIP_TEMPLATE = """AIP|1||9941778^{lastName}^{firstName}^W^^^^^EPIC^^^^PROVID|1.1^Primary|GEN|{schedule_date}{scheduled_time}|0|S|{duration}|S
AIP|2||99225747^{lastName}^{firstName}^E^^^^^EPIC^^^^PROVID|4.20^Circulator||{schedule_date}{scheduled_time}|0|S|{duration}|S
AIP|3||99252693^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|4.150^Scrub ||{schedule_date}{scheduled_time}|0|S|{duration}|S
AIP|4||99252694^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.20^ANE CRNA||{schedule_date}{scheduled_time}|0|S|{duration}|S
AIP|5||99252695^{lastName}^{firstName}^L^^^^^^EPIC^^^^PROVID|2.139^Anesthesiologist||{schedule_date}{scheduled_time}|0|S|{duration}|S"""

# Case event structure
CASE_EVENTS = [
    ("arrive", -60),
    ("in_preop", -45),
    ("out_preop", -15),
    ("planned_preop", -5),
    ("setup", 0),
    ("intraop", 10),
    ("started", 15),
    ("closing", "duration_minus_30"),
    ("complete", "duration_minus_15"),
    ("exiting", "duration_minus_10"),
    ("ordered_pacu", "duration_minus_5"),
    ("planned_pacu", 0),
    ("in_pacu", 5),
    ("out_pacu", 90)
]

def prompt(message, default=None):
    res = input(message)
    return res.strip() if res.strip() else default

def format_hl7_time(dt):
    return dt.strftime("%y%m%d%H%M")

def create_output_directory():
    now = datetime.now()
    dir_name = now.strftime("%y%m%d") + " - HL7 Output"
    os.makedirs(dir_name, exist_ok=True)
    return dir_name

def generate_event_times(base_time, duration):
    events = {}
    for name, offset in CASE_EVENTS:
        if isinstance(offset, int):
            offset_minutes = offset + random.randint(-15, 15) if offset != 0 else 0
        else:
            base = duration - int(offset.split("_")[-1])
            offset_minutes = base + random.randint(-15, 15)
        event_time = base_time + timedelta(minutes=offset_minutes)
        events[name] = event_time
    return events

def generate_hl7_message(event_name, event_time, patient_info, procedure_data, duration, idx=1):
    obx_block = ""
    if event_name != "setup":  # skip OBX only for initial S12
        obx_block = OBX_TEMPLATE.format(
            eventName=event_name,
            event_time=format_hl7_time(event_time)
        )

    # AIS/NTE/AIP blocks for one or two procedures
    ais_block = ""
    nte_block = ""
    aip_block = ""

    for i, proc in enumerate(procedure_data, start=1):
        ais_block += AIS_TEMPLATE.format(
            idx=i,
            procedureId=2753 + i,
            procedure=proc["name"],
            schedule_date=patient_info["YYMMDD"],
            scheduled_time=patient_info["scheduledTime"].replace(":", "")
        ) + "\n"

        nte_block += NTE_TEMPLATE.format(
            procedureDescription=proc["description"],
            specialNeeds=proc["specialNeeds"]
        ) + "\n"

    aip_block = AIP_TEMPLATE.format(
        lastName=patient_info["patientLastName"],
        firstName=patient_info["patientFirstName"],
        schedule_date=patient_info["YYMMDD"],
        scheduled_time=patient_info["scheduledTime"].replace(":", ""),
        duration=duration
    )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return HL7_TEMPLATE.format(
        timestamp=timestamp,
        patientMRN=patient_info["patientMRN"],
        patientFirstName=patient_info["patientFirstName"],
        patientLastName=patient_info["patientLastName"],
        schedule_date=patient_info["YYMMDD"],
        scheduled_time=patient_info["scheduledTime"].replace(":", ""),
        eventName=event_name,
        duration=duration,
        procedure=procedure_data[0]["name"],
        locationDepartment=patient_info["locationDepartment"],
        locationOR=patient_info["locationOR"],
        obx_block=obx_block.strip(),
        ais_block=ais_block.strip(),
        nte_block=nte_block.strip(),
        aip_block=aip_block.strip()
    )

def main():
    print("\n📝 Let's gather info for this patient's procedure.\n")

    # Required info
    patientLastName = prompt("What's the patient's last name?")
    patientFirstName = prompt("What's the patient's first name?")
    patientMRN = prompt("Change the patient's MRN? (Default is no) y/n? ")
    patientMRN = patientMRN if patientMRN and patientMRN.lower() != 'n' else str(random.randint(9000000, 9999999))
    
    YYMMDD = prompt("Schedule the date of the procedure? (Format is YYMMDD) y/n? ")
    YYMMDD = YYMMDD if YYMMDD and YYMMDD.lower() != 'n' else datetime.now().strftime("%y%m%d")
    
    scheduledTime = prompt("What's the setup time of the procedure? (Format is HH:MM)")
    locationDepartment = prompt("What department should this be scheduled for?")
    locationOR = prompt("What OR room should this be scheduled for?")

    # Procedure(s)
    procedures = []
    while True:
        name = prompt("What's the procedure name?")
        description = prompt("What's the procedure description?")
        specialNeeds = prompt("Are there any special needs for this procedure? If yes, enter it now otherwise leave blank.")

        procedures.append({
            "name": name,
            "description": description,
            "specialNeeds": specialNeeds
        })

        multi = prompt("Is this a multi-procedure case? Would you like to schedule an additional case for this patient? y/n ")
        if multi.lower() != 'y':
            break

    # Duration and event times
    base_time = datetime.strptime(f"{YYMMDD}{scheduledTime.replace(':', '')}", "%y%m%d%H%M")
    duration = random.randint(90, 180)
    event_times = generate_event_times(base_time, duration)

    # Output
    output_dir = create_output_directory()
    patient_info = {
        "patientFirstName": patientFirstName,
        "patientLastName": patientLastName,
        "patientMRN": patientMRN,
        "YYMMDD": YYMMDD,
        "scheduledTime": scheduledTime,
        "locationDepartment": locationDepartment,
        "locationOR": locationOR
    }

    filenames = []
    # S12 scheduling message first
    s12_message = generate_hl7_message("setup", base_time, patient_info, procedures, duration)
    filenames.append(f"{patientFirstName}{patientLastName}-00.hl7")
    with open(os.path.join(output_dir, filenames[-1]), "w") as f:
        f.write(s12_message)

    for idx, (event, _) in enumerate(CASE_EVENTS):
        if event == "setup":
            continue
        msg = generate_hl7_message(event, event_times[event], patient_info, procedures, duration)
        filename = f"{patientFirstName}{patientLastName}-{idx:02}.hl7"
        filenames.append(filename)
        with open(os.path.join(output_dir, filename), "w") as f:
            f.write(msg)

    print(f"\n✅ HL7 messages generated in: {output_dir}")
    for file in filenames:
        print(f" - {file}")

if __name__ == "__main__":
    main()
