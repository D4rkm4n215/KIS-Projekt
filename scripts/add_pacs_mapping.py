import requests
import json
import urllib3
import uuid  # Neu hinzugefügt für die Generierung von UUIDs

# SSL Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
SOURCE_NAME = "PACS Procedure Code"
VERIFY_SSL = False
SAME_AS_MAP_TYPE = "SAME-AS"

def get_resource(endpoint, params=None):
    response = requests.get(f"{BASE_URL}/{endpoint}", auth=AUTH, params=params, verify=VERIFY_SSL)
    return response.json() if response.status_code == 200 else None

def post_resource(endpoint, payload):
    response = requests.post(f"{BASE_URL}/{endpoint}", auth=AUTH, json=payload, headers=HEADERS, verify=VERIFY_SSL)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Fehler bei POST {endpoint}: {response.status_code} - {response.text}")
        return None

def setup_radiology_mapping(concept_display_name):
    print(f"\n--- Verarbeite: {concept_display_name} ---")

    # 1. Sicherstellen, dass die Concept Source existiert
    source = get_resource("conceptsource", {"q": SOURCE_NAME})
    if not source or not source['results']:
        print(f"Erstelle Concept Source: {SOURCE_NAME}...")
        source = post_resource("conceptsource", {"name": SOURCE_NAME, "description": "Source for PACS Codes"})
        source_uuid = source['uuid']
    else:
        source_uuid = source['results'][0]['uuid']

    # 2. Konzept abrufen (mit allen Mappings)
    concept_search = get_resource("concept", {"q": concept_display_name, "v": "full"})
    if not concept_search or not concept_search['results']:
        print(f"FEHLER: Konzept '{concept_display_name}' nicht gefunden.")
        return

    concept_data = concept_search['results'][0]
    concept_uuid = concept_data['uuid']
    existing_mappings = concept_data.get('mappings', [])
    
    # Prüfen, ob bereits ein Mapping für diese Source existiert
    already_mapped = False
    updated_mappings = []
    
    for m in existing_mappings:
        ref_term = m.get('conceptReferenceTerm')
        if not ref_term: continue
        
        # Mapping für Payload sichern
        updated_mappings.append({
            "conceptReferenceTerm": ref_term['uuid'],
            "conceptMapType": m['conceptMapType']['uuid']
        })
        
        # Check ob unsere Source schon gemappt ist
        source_ref = ref_term.get('conceptSource')
        # In 'full' Ansicht ist conceptSource oft ein Objekt
        source_name_current = source_ref.get('display') if isinstance(source_ref, dict) else ""
        
        if SOURCE_NAME in source_name_current:
            already_mapped = True

    if already_mapped:
        print(f"Info: {concept_display_name} hat bereits ein PACS-Mapping. Überspringe...")
        return

    # 3. Neuen Reference Term erstellen (Code = UUID, Name = Konzeptname)
    new_pacs_code = str(uuid.uuid4()) # Generiert eine zufällige UUID
    print(f"Erstelle neuen Term: Name='{concept_display_name}', Code='{new_pacs_code}'")
    
    term_payload = {
        "code": new_pacs_code,
        "name": concept_display_name, # Hier wird der Name des Konzeptes gesetzt
        "conceptSource": source_uuid
    }
    
    new_term = post_resource("conceptreferenceterm", term_payload)
    if not new_term:
        return

    # 4. Mapping zum Konzept hinzufügen
    updated_mappings.append({
        "conceptReferenceTerm": new_term['uuid'],
        "conceptMapType": SAME_AS_MAP_TYPE
    })

    if post_resource(f"concept/{concept_uuid}", {"mappings": updated_mappings}):
        print(f"ERFOLG: Mapping für {concept_display_name} mit UUID-Code erstellt.")

def get_radiology_orders():
    CONCEPT_NAME = "All Radiology orders"
    # 1. Suche nach dem Haupt-Konzept
    print(f"Suche nach Konzept: {CONCEPT_NAME}...")
    search_url = f"{BASE_URL}/concept"
    params = {'q': CONCEPT_NAME, 'v': 'full'} # 'full' ist wichtig für setMembers
    
    response = requests.get(search_url, auth=AUTH, params=params, verify=VERIFY_SSL)
    
    if response.status_code != 200:
        print(f"Fehler beim Abruf: {response.status_code}")
        return

    results = response.json().get('results', [])
    if not results:
        print("Kein Konzept mit diesem Namen gefunden.")
        return

    # Wir nehmen das erste Ergebnis
    concept_data = results[0]
    members = concept_data.get('setMembers', [])

    if not members:
        print(f"Das Konzept '{CONCEPT_NAME}' hat keine Mitglieder (setMembers).")
        return

    print(f"\nGefundene Einträge in '{CONCEPT_NAME}':")
    print("-" * 60)
    print(f"{'Name':<40} | {'UUID':<36}")
    print("-" * 60)

    for member in members:
        display_name = member.get('display')
        uuid = member.get('uuid')
        print(f"{display_name:<40} | {uuid:<36}")
        
        # Falls du tiefer gehen willst (Untergruppen):
        # get_members_recursive(uuid, level=1)

# --- START ---
# Da wir die Codes nun generieren, brauchen wir nur noch die Namen der Konzepte
concepts_to_process = [
    "X-ray of abdomen, 2 views (AP supine and lateral decubitus)"
]

for name in concepts_to_process:
    setup_radiology_mapping(name)