import requests
import os
import pandas as pd
import urllib3

# SSL Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
BASE_URL = "https://localhost/openmrs/ws/rest/v1/concept"
AUTH = ("superman", "Admin123")
HEADERS = {"Content-Type": "application/json"}
VERIFY_SSL = False

def get_to_keep_laboratory_orders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Laborwerte_zum_behalten.xlsx')
    df = pd.read_excel(file_path)
    df = df.dropna()
    return df


def update_fsn_only(df):
    """
    Iteriert durch den DataFrame und ändert NUR den Fully Specified Name (FSN).
    """
    print("🚀 Starte Update der Fully Specified Names (FSN)...")
    print("-" * 60)

    updated_count = 0
    error_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        concept_uuid = str(row['UUID']).strip()
        new_name = str(row['Neuer Name']).strip()
        
        # Sicherheitschecks
        if pd.isna(row['Neuer Name']) or new_name == "" or new_name.lower() == "nan":
            skipped_count += 1
            continue
        try:
            # 1. Konzept laden
            custom_view = "custom:(uuid,display,names:(uuid,name,display,conceptNameType,locale))"
                
            get_url = f"{BASE_URL}/{concept_uuid}"
            params = {'v': custom_view}
            response = requests.get(get_url, auth=AUTH, verify=VERIFY_SSL, params=params)
            
            if response.status_code != 200:
                print(f"❌ Fehler: Konzept {concept_uuid} nicht gefunden.")
                error_count += 1
                continue

            concept_data = response.json()
            names_list = concept_data.get('names', [])
            
            # 2. Den FSN in der Liste suchen
            fsn_uuid = None
            current_fsn_name = None
            
            for n in names_list:
                # Wir suchen explizit nach dem Typ FULLY_SPECIFIED
                # Optional: and n.get('locale') == 'en' hinzufügen, wenn Sie strikt sein wollen
                if n.get('conceptNameType') == 'FULLY_SPECIFIED':
                    fsn_uuid = n.get('uuid')
                    current_fsn_name = n.get('display') # oder n.get('name')
                    break 
            
            if not fsn_uuid:
                print(f"⚠️  Warnung: Konzept {concept_uuid} hat keinen FSN (sehr ungewöhnlich).")
                error_count += 1
                continue

            # Check: Ist der Name schon richtig?
            if current_fsn_name == new_name:
                print(f"ℹ️  Skippe: '{current_fsn_name}' ist bereits aktuell.")
                skipped_count += 1
                continue

            print(f"🔄 Ändere FSN: '{current_fsn_name}' -> '{new_name}'")

            # 3. Update Request an die spezifische Namens-UUID senden
            update_url = f"{BASE_URL}/{concept_uuid}/name/{fsn_uuid}"
            
            payload = {
                "name": new_name
            }
            
            update_response = requests.post(
                update_url, 
                json=payload, 
                auth=AUTH, 
                verify=VERIFY_SSL, 
                headers={'Content-Type': 'application/json'}
            )

            if update_response.status_code == 200:
                print(f"   ✅ Erfolg!")
                updated_count += 1
            else:
                # Häufiger Fehler: Name existiert schon bei einem anderen Konzept
                print(f"   ❌ API Fehler: {update_response.status_code} - {update_response.text}")
                error_count += 1
        except Exception as e:
            print(f"❌ Fehler beim Update von {concept_uuid}: {str(e)}")
            error_count += 1

    print("-" * 60)
    print(f"🏁 FSN Update Fertig. Aktualisiert: {updated_count} | Fehler: {error_count} | Übersprungen: {skipped_count}")


if __name__ == "__main__":
    df = get_to_keep_laboratory_orders()
    update_fsn_only(df)