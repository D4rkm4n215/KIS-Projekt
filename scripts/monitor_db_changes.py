import mysql.connector
import time

# --- KONFIGURATION DATENBANK ---
# Passen Sie diese Werte an Ihre lokale Docker/MySQL Umgebung an
DB_CONFIG = {
    'user': 'openmrs-user',           # Oft 'root' im Docker Container
    'password': 'password',   # Standard Bahmni/OpenMRS DB Passwort oft 'password'
    'host': 'localhost',      # Oder '127.0.0.1'
    'port': 3307,             # Standard Port (in docker-compose prüfen!)
    'database': 'openmrs'     # Name der DB
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Fehler bei DB-Verbindung: {err}")
        print("   Tipp: Prüfen Sie Port (Docker Mapping?) und Passwort.")
        return None

def get_all_table_counts(conn):
    """Holt die exakte Zeilenanzahl für ALLE Tabellen."""
    cursor = conn.cursor()
    
    # 1. Alle Tabellennamen holen
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    
    counts = {}
    print(f"   Scanne {len(tables)} Tabellen...", end="", flush=True)
    
    # 2. Zeilen für jede Tabelle zählen
    for i, table in enumerate(tables):
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            counts[table] = count
        except:
            pass # Views oder Berechtigungsprobleme ignorieren
            
    print(" Fertig.")
    cursor.close()
    return counts

def print_diff(old_counts, new_counts):
    print("\n" + "="*60)
    print("📊 VERÄNDERUNGEN IN DER DATENBANK")
    print("="*60)
    
    changes_found = False
    
    # Wir sortieren die Ausgabe, damit 'patient' und 'encounter' gruppiert sind
    all_tables = sorted(new_counts.keys())
    
    for table in all_tables:
        old = old_counts.get(table, 0)
        new = new_counts.get(table, 0)
        diff = new - old
        
        if diff != 0:
            changes_found = True
            # Schöne Formatierung: Grün für Plus, Rot für Minus
            sign = "+" if diff > 0 else ""
            print(f" • {table:<40} : {old:>5} -> {new:>5}  ({sign}{diff})")
            
    if not changes_found:
        print("   Keine Änderungen festgestellt.")
    print("="*60 + "\n")

def main():
    conn = get_db_connection()
    if not conn: return

    print("\n--- SCHRITT 1: BASIS-ZUSTAND ERFASSEN ---")
    print("Lese Datenbank...")
    baseline = get_all_table_counts(conn)
    
    print(f"✅ Basislinie erstellt ({len(baseline)} Tabellen erfasst).")
    print("\n" + "-"*50)
    input("👉 BITTE JETZT IHR IMPORT-SKRIPT AUSFÜHREN.\n   Drücken Sie danach [ENTER] hier in der Konsole...")
    print("-"*50 + "\n")
    
    print("--- SCHRITT 2: NEUEN ZUSTAND ERFASSEN ---")
    # Verbindung erneuern, um sicherzustellen, dass Caches leer sind
    conn.reconnect() 
    current = get_all_table_counts(conn)
    
    print_diff(baseline, current)
    conn.close()

if __name__ == "__main__":
    main()