import requests
import json
import urllib3

# SSL Warnungen für selbstsignierte Zertifikate unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
SOURCE_NAME = "PACS Procedure Code"
VERIFY_SSL = False  # Wichtig für dein selbstsigniertes Zertifikat
CONCEPT_NAME = "All Radiology orders"


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

def get_radiology_orders():
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

def setup_radiology_mapping(concept_display_name, pacs_code):
    print(f"--- Verarbeite: {concept_display_name} ({pacs_code}) ---")

    # 1. Sicherstellen, dass die Concept Source existiert
    source = get_resource(f"conceptsource", {"q": SOURCE_NAME})
    source_uuid = None
    if source and source['results']:
        source_uuid = source['results'][0]['uuid']
    else:
        print(f"Erstelle Concept Source: {SOURCE_NAME}...")
        new_source = post_resource("conceptsource", {"name": SOURCE_NAME, "description": "Source for PACS Codes"})
        source_uuid = new_source['uuid']

    # 2. Sicherstellen, dass der Reference Term existiert
    term_search = get_resource("conceptreferenceterm", {"q": pacs_code, "source": source_uuid})
    term_uuid = None
    
    # Exakte Übereinstimmung prüfen
    if term_search and term_search['results']:
        for result in term_search['results']:
            if result['display'].split(":")[1].strip() == pacs_code: # Format ist oft "Source: Code"
                term_uuid = result['uuid']
                break

    if not term_uuid:
        print(f"Erstelle Reference Term: {pacs_code}...")
        new_term = post_resource("conceptreferenceterm", {
            "code": pacs_code,
            "conceptSource": source_uuid
        })
        if new_term: term_uuid = new_term['uuid']

    # 2. Bestehendes Konzept abrufen, um aktuelle Mappings zu erhalten
    concept_search = get_resource("concept", {"q": concept_display_name, "v": "full"}) # 'v=full' ist wichtig für Mappings
    if not concept_search or not concept_search['results']:
        print(f"Fehler: Konzept '{concept_display_name}' nicht gefunden.")
        return

    concept_data = concept_search['results'][0]
    concept_uuid = concept_data['uuid']
    
    # Bestehende Mappings extrahieren
    existing_mappings = concept_data.get('mappings', [])
    updated_mappings = []
    already_exists = False

    for m in existing_mappings:
        ref_term = m.get('conceptReferenceTerm')
        map_type = m.get('conceptMapType')
        
        # Sicherstellen, dass die nötigen Basis-Daten da sind, um das Mapping zu erhalten
        if not ref_term or not map_type:
            continue

        # Payload für das bestehende Mapping vorbereiten (wir brauchen die UUIDs)
        m_payload = {
            "conceptReferenceTerm": ref_term.get('uuid'),
            "conceptMapType": map_type.get('uuid')
        }
        updated_mappings.append(m_payload)
        
        # Sicherer Check auf den PACS-Code
        # .get('code') gibt None zurück, statt abzustürzen, wenn der Key fehlt
        current_code = ref_term.get('code')
        if current_code == pacs_code:
            already_exists = True

    if already_exists:
        print(f"Info: Mapping für {pacs_code} existiert bereits. Überspringe...")
        return

    # 3. Das neue Mapping zur Liste hinzufügen
    updated_mappings.append({
        "conceptReferenceTerm": term_uuid,
        "conceptMapType": "SAME-AS" # SAME-AS
    })

    # 4. Das Konzept mit der VOLLSTÄNDIGEN Liste aktualisieren
    mapping_payload = {
        "mappings": updated_mappings
    }

    if post_resource(f"concept/{concept_uuid}", mapping_payload):
        print(f"ERFOLG: Mapping für {concept_display_name} hinzugefügt (alte Mappings beibehalten).")


if __name__ == "__main__":
    # --- BEISPIEL-DATEN (Hier kannst du deine CSV-Logik einbauen) ---
    # Format: ("Name in Bahmni", "PACS Code")

    # get_radiology_orders()
    data_to_map = [
        ("X-ray of abdomen, 2 views (AP supine and lateral decubitus)", "X-ray of abdomen, 2 views (AP supine and lateral decubitus)"),
    ]
    for bahmni_name, code in data_to_map:
        setup_radiology_mapping(bahmni_name, code)