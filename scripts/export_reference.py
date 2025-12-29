import requests
import json
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
# Geben Sie hier den Namen des Patienten ein, den Sie MANUELL in Bahmni angelegt haben
SEARCH_NAME = "Maria Mustermann" 

API_URL = 'https://localhost/openmrs/ws/fhir2/R4'
AUTH = ('superman', 'Admin123')

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Gespeichert: {filename}")

def export_patient_data():
    print(f"--- Suche nach '{SEARCH_NAME}' ---")
    
    # 1. Patient suchen
    r = requests.get(f"{API_URL}/Patient", params={'name': SEARCH_NAME}, auth=AUTH, verify=False)
    bundle = r.json()
    
    if not bundle.get('entry'):
        print("Kein Patient gefunden! Haben Sie ihn in Bahmni angelegt?")
        return

    # Wir nehmen den ersten Treffer
    patient_res = bundle['entry'][0]['resource']
    pat_id = patient_res['id']
    print(f"Gefunden: {patient_res['name'][0]['given'][0]} {patient_res['name'][0]['family']} (UUID: {pat_id})")
    
    # Patient speichern
    save_json(f"export_patient_{pat_id}.json", patient_res)

    # 2. Encounters laden
    print("\n--- Lade Encounters (Besuche) ---")
    r = requests.get(f"{API_URL}/Encounter", params={'subject': f"Patient/{pat_id}"}, auth=AUTH, verify=False)
    enc_bundle = r.json()
    
    if enc_bundle.get('entry'):
        for i, entry in enumerate(enc_bundle['entry']):
            enc = entry['resource']
            enc_id = enc['id']
            # Encounter speichern
            save_json(f"export_encounter_{i}_{enc_id}.json", enc)
            
            # WICHTIG: Analyse des Participants (Provider)
            print(f"Encounter {i} ({enc.get('class', {}).get('code', 'Keine Klasse')}):")
            if 'participant' in enc:
                print(json.dumps(enc['participant'], indent=2))
            else:
                print("  Kein Participant Block vorhanden.")
    else:
        print("Keine Encounter für diesen Patienten gefunden.")

if __name__ == "__main__":
    export_patient_data()