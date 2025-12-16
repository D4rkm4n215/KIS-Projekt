import json
import uuid
import argparse
import requests
import urllib3

# SSL Warnungen bei localhost unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
DEFAULT_INPUT = '0001310848.json'
DEFAULT_OUTPUT = 'bahmni_transaction_bundle.json'

# API Zugangsdaten für den Live-Lookup
DEFAULT_API_URL = 'https://localhost/openmrs/ws/rest/v1'
DEFAULT_USER = 'superman'
DEFAULT_PASS = 'Admin123'

# 1. PATIENT (Ihre ermittelte ID UUID)
DEFAULT_ID_UUID = 'd3153eb0-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ID_NAME = 'Patient Identifier'

# 2. ENCOUNTER (Ihre ermittelte Encounter UUID)
# Bitte hier die UUID eintragen, die Sie zuletzt benutzt haben!
DEFAULT_ENC_UUID = 'd34fe3ab-5e07-11ef-8f7c-0242ac120002' 
DEFAULT_ENC_NAME = 'Consultation'

# 3. OBSERVATION (NEU: Hier UUID aus check_concepts.py eintragen)
# Platzhalter UUID - BITTE ERSETZEN!
DEFAULT_OBS_UUID = '160531AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' 
DEFAULT_OBS_NAME = 'Chief complaint (text)' 

# Fallback Diagnose (falls ICD-10 Code nicht gefunden wird)
DEFAULT_COND_UUID = 'd3686b3c-5e07-11ef-8f7c-0242ac120002' # Coded Diagnosis (bitte anpassen!)
DEFAULT_COND_NAME = 'Coded Diagnosis'

# 2. NEUE PFLICHTFELDER FÜR ENCOUNTER (Bitte anpassen!)
DEFAULT_LOC_UUID = '5e232c47-8ff5-4c5c-8057-7e39a64fefa5' # z.B. für "OPD"
DEFAULT_LOC_NAME = 'OPD-1'

concept_cache = {}

def get_concept_uuid_by_code(code, api_url, auth, fallback_uuid):
    if not code or code == '?': return fallback_uuid, "Unknown"
    if code in concept_cache: return concept_cache[code]
    try:
        response = requests.get(f"{api_url}/concept", params={'q': code, 'v': 'custom:(uuid,display)'}, auth=auth, verify=False)
        results = response.json().get('results', [])
        if results:
            concept_cache[code] = (results[0]['uuid'], results[0].get('display', code))
            return concept_cache[code]
    except: pass
    return fallback_uuid, "Fallback Diagnosis"

def convert_to_transaction(args):
    try:
        with open(args.input, 'r', encoding='utf-8') as f: data = json.load(f)
    except: return

    auth = (args.user, args.password)
    transaction_bundle = { "resourceType": "Bundle", "type": "transaction", "entry": [] }
    id_map = {}

    for entry in data.get('entry', []):
        res = entry.get('resource')
        if res and res.get('id'):
            id_map[f"{res.get('resourceType')}/{res.get('id')}"] = f"urn:uuid:{uuid.uuid4()}"

    print(f"Konvertiere OHNE Provider (für Stabilität)...")

    for entry in data.get('entry', []):
        res = entry.get('resource')
        if not res: continue
        rtype = res.get('resourceType')
        old_id = res.get('id')

        if rtype == 'Patient':
            res['name'] = [{"use": "official", "family": args.family, "given": [args.given]}]
            res['active'] = True
            old_val = res.get('identifier', [{}])[0].get('value', 'Unknown')
            res['identifier'] = [{"use": "official", "type": { "coding": [{"code": args.id_uuid}], "text": args.id_name }, "value": old_val}]
            keys_to_del = []
            if 'address' in res:
                del res['address']
            for k in set(keys_to_del): 
                for addr in res.get('address', []): 
                    if k in addr: del addr[k]

        elif rtype == 'Encounter':
            res['status'] = 'finished'
            res['type'] = [{"coding": [{"system": "http://fhir.openmrs.org/code-system/encounter-type", "code": args.enc_uuid, "display": args.enc_name}], "text": args.enc_name}]
            res['class'] = { "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory" }
            if 'serviceType' in res: del res['serviceType']
            
            # Location ist wichtig und bleibt
            res['location'] = [{"location": { "reference": f"Location/{args.loc_uuid}", "display": args.loc_name }}]

            # --- STABILITÄTS-FIX: KEIN PROVIDER/PARTICIPANT ---
            if 'participant' in res:
                del res['participant']
            # --------------------------------------------------

        elif rtype == 'Observation':
            res['status'] = 'final'
            res['code'] = { "coding": [{"code": args.obs_uuid, "display": args.obs_name}], "text": args.obs_name }
            if 'valueCodeableConcept' in res:
                orig = "?"
                try: orig = res['valueCodeableConcept']['coding'][0].get('code', '?')
                except: pass
                del res['valueCodeableConcept']
                res['valueString'] = f"Vitalstatus Code: {orig}"
            if 'effectiveDateTime' not in res and 'issued' in res: res['effectiveDateTime'] = res['issued']

        elif rtype == 'Condition':
            icd = None
            try: icd = res['code']['coding'][0].get('code')
            except: pass
            real_uuid, real_name = get_concept_uuid_by_code(icd, args.api_url, auth, args.cond_uuid)
            res['code'] = {"coding": [{"code": real_uuid, "display": real_name}], "text": real_name}
            if 'note' not in res: res['note'] = []
            res['note'].append({"text": f"Original Import Code: {icd}"})

        if 'id' in res: del res['id']
        if 'meta' in res: del res['meta']
        
        res_str = json.dumps(res)
        for k, v in id_map.items(): res_str = res_str.replace(k, v)
        new_res = json.loads(res_str)
        full_url = id_map.get(f"{rtype}/{old_id}") or f"urn:uuid:{uuid.uuid4()}"
        
        transaction_bundle['entry'].append({
            "fullUrl": full_url, "resource": new_res, "request": {"method": "POST", "url": rtype}
        })

    with open(args.output, 'w', encoding='utf-8') as f: json.dump(transaction_bundle, f, indent=2)
    print("Fertig! Sauberes Bundle erstellt.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=DEFAULT_INPUT)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    parser.add_argument('--api-url', default=DEFAULT_API_URL)
    parser.add_argument('--user', default=DEFAULT_USER)
    parser.add_argument('--password', default=DEFAULT_PASS)
    parser.add_argument('--family', default="Mustermann")
    parser.add_argument('--given', default="Maria")
    parser.add_argument('--id-uuid', default=DEFAULT_ID_UUID)
    parser.add_argument('--id-name', default=DEFAULT_ID_NAME)
    parser.add_argument('--enc-uuid', default=DEFAULT_ENC_UUID)
    parser.add_argument('--enc-name', default=DEFAULT_ENC_NAME)
    parser.add_argument('--obs-uuid', default=DEFAULT_OBS_UUID)
    parser.add_argument('--obs-name', default=DEFAULT_OBS_NAME)
    parser.add_argument('--cond-uuid', default=DEFAULT_COND_UUID)
    parser.add_argument('--loc-uuid', default=DEFAULT_LOC_UUID)
    parser.add_argument('--loc-name', default=DEFAULT_LOC_NAME)
    
    # Provider wird ignoriert
    parser.add_argument('--prov-uuid', default="")
    parser.add_argument('--prov-name', default="")
    
    args = parser.parse_args()
    convert_to_transaction(args)