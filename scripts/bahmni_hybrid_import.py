import requests
import json
import urllib3
import sys
import argparse
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
INPUT_FILE = '0002690836.json'
BASE_URL = 'https://localhost/openmrs'
AUTH = ('superman', 'Admin123')

# URLs
URL_FHIR = f"{BASE_URL}/ws/fhir2/R4"
URL_REST = f"{BASE_URL}/ws/rest/v1"

# --- UUIDs & NAMEN (Aus convert_bundle.py übernommen) ---
ID_TYPE_UUID    = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
ID_TYPE_NAME    = 'Patient Identifier'  # <--- WICHTIG für FHIR Validierung

ENC_TYPE_UUID   = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
LOCATION_UUID   = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5' 
VISIT_TYPE_UUID = '54f43754-c6ce-4472-890e-0f28acaeaea6' 
PROVIDER_UUID   = 'd7a67c17-5e07-11ef-8f7c-0242ac120002' 
ROLE_UUID       = 'a0b03050-c99b-11e0-9572-0800200c9a66' 
OBS_CHIEF_COMPLAINT_UUID = '160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 

# Cache
concept_cache = {}

def resolve_concept_uuid(code):
    if not code: return None
    if code in concept_cache: return concept_cache[code]
    try:
        # REST Lookup ist einfacher und stabiler
        r = requests.get(f"{URL_REST}/concept", params={'q': code, 'v': 'custom:(uuid,display)'}, auth=AUTH, verify=False)
        if r.status_code == 200 and r.json().get('results'):
            res = r.json()['results'][0]
            print(f"      ✅ ICD '{code}' -> UUID {res['uuid']}")
            concept_cache[code] = res['uuid']
            return res['uuid']
    except: pass
    print(f"      ⚠️  Keine UUID für '{code}' gefunden.")
    return None

def run_import(args):
    print(f"📂 Lese {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        print("❌ Datei nicht gefunden."); sys.exit(1)

    print(f"🚀 HYBRID IMPORT V3 für: {args.given} {args.family}")

    # Datensammler
    source_patient = None
    source_conditions = []
    source_encounters = [] 
    source_obs_text = "Routine Checkup"

    # 1. Parsing
    for entry in data.get('entry', []):
        res = entry.get('resource', {})
        rtype = res.get('resourceType')

        if rtype == 'Patient':
            source_patient = res
        elif rtype == 'Condition':
            source_conditions.append(res)
        elif rtype == 'Encounter':
            per = res.get('period', {})
            if per.get('start'):
                source_encounters.append({'start': per['start'], 'end': per.get('end', per['start'])})
        elif rtype == 'Observation':
            if res.get('code', {}).get('text'):
                source_obs_text = res['code']['text']
            
    if not source_patient:
        print("❌ Kein Patient in der Datei."); sys.exit(1)

    source_encounters.sort(key=lambda x: x['start'])
    if not source_encounters:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")
        source_encounters.append({'start': now, 'end': now})

    # ---------------------------------------------------------
    # PHASE 1: PATIENT (FHIR) - Fix für "Select a preferred identifier"
    # ---------------------------------------------------------
    print("\n[1] Patient (FHIR)...")
    headers = {'Content-Type': 'application/fhir+json'}
    
    # ID Wert holen
    pat_id_val = source_patient.get('identifier', [{}])[0].get('value', 'Unknown')
    
    # Check via REST
    r_check = requests.get(f"{URL_REST}/patient", params={'q': pat_id_val, 'v': 'full'}, auth=AUTH, verify=False)
    patient_uuid = None
    
    if r_check.json().get('results'):
        patient_uuid = r_check.json()['results'][0]['uuid']
        print(f"   ✅ Patient existiert bereits: {patient_uuid}")
    else:
        # HIER IST DER FIX: Struktur exakt wie in convert_bundle.py
        fhir_pat = {
            "resourceType": "Patient",
            "active": True,
            "name": [{"use": "official", "family": args.family, "given": [args.given]}],
            "gender": source_patient.get('gender', 'male').lower(),
            "birthDate": source_patient.get('birthDate', '1980-01-01'),
            "identifier": [{
                "use": "official",
                "type": {
                    "coding": [{"code": ID_TYPE_UUID}], # KEIN 'system' URL, nur Code!
                    "text": ID_TYPE_NAME                # Text ist wichtig!
                },
                "value": pat_id_val
            }]
        }
        
        r_create = requests.post(f"{URL_FHIR}/Patient", json=fhir_pat, headers=headers, auth=AUTH, verify=False)
        if r_create.status_code in [200, 201]:
            patient_uuid = r_create.json()['id']
            print(f"   ✅ Patient erstellt: {patient_uuid}")
        else:
            print(f"   ❌ Fehler Patient: {r_create.text}"); sys.exit(1)

    # ---------------------------------------------------------
    # PHASE 2: CONDITIONS (FHIR) - Struktur wie im Bundle
    # ---------------------------------------------------------
    print("\n[2] Conditions (FHIR)...")
    
    for cond_res in source_conditions:
        orig_code = None
        try: orig_code = cond_res['code']['coding'][0]['code']
        except: pass
        
        if not orig_code: continue
        
        real_uuid = resolve_concept_uuid(orig_code)
        if not real_uuid: continue

        # Datum holen: Erst recordedDate versuchen, dann onsetDateTime, dann Heute
        # Das Dashboard mag 'recordedDate' lieber!
        date_val = cond_res.get('recordedDate') 
        if not date_val:
            date_val = cond_res.get('onsetDateTime')
        if not date_val:
            date_val = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00") # ISO Format sicherstellen

        # FIX: Struktur exakt an das funktionierende Beispiel angepasst
        fhir_condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
            },
            "verificationStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
            },
            "code": {
                # WICHTIG: KEIN 'system' Feld hier! Nur code und display.
                "coding": [{"code": real_uuid, "display": orig_code}],
                "text": orig_code
            },
            "subject": { "reference": f"Patient/{patient_uuid}" },
            
            # WICHTIG: 'recordedDate' statt nur 'onsetDateTime' verwenden
            "recordedDate": date_val,
            
            "note": [{"text": f"Original Import Code: {orig_code}"}]
        }

        r_cond = requests.post(f"{URL_FHIR}/Condition", json=fhir_condition, auth=AUTH, verify=False)
        if r_cond.status_code in [200, 201]:
            print(f"   ✅ Condition '{orig_code}' OK.")
        else:
            print(f"   ❌ Fehler Condition '{orig_code}': {r_cond.text}")

    # ---------------------------------------------------------
    # PHASE 3: ENCOUNTERS (REST) - Stabil
    # ---------------------------------------------------------
    print("\n[3] Encounters (REST)...")
    
    for enc in source_encounters:
        print(f"   -> Besuch am {enc['start']}...")
        
        # A. Visit
        v_payload = {
            "patient": patient_uuid, "visitType": VISIT_TYPE_UUID, 
            "startDatetime": enc['start'], "stopDatetime": enc['end'], "location": LOCATION_UUID
        }
        r_v = requests.post(f"{URL_REST}/visit", json=v_payload, auth=AUTH, verify=False)
        if r_v.status_code > 201: print(f"      ❌ Visit Fehler: {r_v.text}"); continue
        
        # B. Encounter
        e_payload = {
            "encounterDatetime": enc['start'],
            "patient": patient_uuid, "encounterType": ENC_TYPE_UUID, 
            "location": LOCATION_UUID, "visit": r_v.json()['uuid'],
            "encounterProviders": [{"provider": PROVIDER_UUID, "encounterRole": ROLE_UUID}],
            "obs": [{"concept": OBS_CHIEF_COMPLAINT_UUID, "value": source_obs_text}]
        }
        r_e = requests.post(f"{URL_REST}/encounter", json=e_payload, auth=AUTH, verify=False)
        if r_e.status_code > 201: print(f"      ❌ Encounter Fehler: {r_e.text}")
        else: print(f"      ✅ OK.")

    print(f"\n🎉 FERTIG!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--given', default="Max")
    parser.add_argument('--family', default="Mustermann")
    run_import(parser.parse_args())