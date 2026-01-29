# studiKIS 🏥

**studiKIS** ist eine spezialisierte Instanz von **Bahmni**, die am **Institut für Medizinische Informatik (IMI) des Universitätsklinikums Heidelberg** konfiguriert und weiterentwickelt wurde. Das Projekt optimiert die Bahmni-Plattform für die klinische Forschung und Lehre.

Es kombiniert OpenMRS (Patientenakten), OpenELIS (Labormanagement) und Bahmni (UI), um ein integriertes Krankenhausinformationssystem (KIS) bereitzustellen.

---

## 🚀 Features

* **Zentrale Patientenverwaltung:** Erfassung von Stammdaten und Behandlungsverläufen.
* **Klinische Dokumentation:** Unterstützung für Diagnosen, Medikation und Verläufe.
* **Labor-Integration:** Anbindung an OpenELIS.
* **PACS/DICOM Anbindung:** Unterstützung für medizinische Bildgebung.

## 🛠 Technologien

* **Basis:** [Bahmni Standard Docker Distribution](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/2990407691/Bahmni+Standard+Deployment+with+Docker)
* **Backend:** Java (OpenMRS), Groovy, Python
* **Frontend:** JavaScript (AngularJS)
* **Konfiguration:** JSON/App-Descriptors in `/standard-config`

## 📂 Projektstruktur

* `/standard-config`: Die studiKIS-spezifischen Konfigurationsdateien.
* `/scripts`: Hilfsskripte für die Umgebung.

## ⚙️ Installation & Setup

Dieses Setup nutzt die offizielle Bahmni-Distribution, ersetzt jedoch die Standard-Konfiguration durch die studiKIS-Inhalte.

### 1. Repositories klonen
Klonen Sie das Bahmni-Basis-Repo und dieses Konfigurations-Repo:

```bash
# Bahmni Docker Basis
git clone https://github.com/Bahmni/bahmni-docker.git
cd bahmni-docker/bahmni-standard

# studiKIS Konfiguration (dieses Repo)
git clone https://github.com/IMI-HD/studiKIS.git
```

### 2. Bahmni-Config Service deaktivieren
Um die lokale Konfiguration nutzen zu können, muss der Standard-Config-Service in der `docker-compose.yml` auskommentiert werden:

```yaml
# In der docker-compose.yml folgende Zeilen auskommentieren:
# bahmni-config:
#   image: 'bahmni/standard-config:${CONFIG_IMAGE_TAG:?}'
#   volumes:
#     - '${CONFIG_VOLUME:?}:/usr/local/bahmni_config'
#   logging: *log-config
#   restart: ${RESTART_POLICY}
```

### 3. Umgebungsvariablen (.env) anpassen
Öffnen Sie die Datei `.env` im Verzeichnis `bahmni-standard` und führen Sie folgende Änderungen durch:

1. **Profile aktivieren:**
   ```bash
   COMPOSE_PROFILES=bahmni-standard,metabase
   ```

2. **Pfad zur studiKIS-Config hinterlegen:**
   Hinterlegen Sie bei `CONFIG_VOLUME` den Pfad zum `standard-config` Ordner aus dem geklonten studiKIS-Repo:
   ```bash
   # Bahmni Config Environment Variables
   CONFIG_IMAGE_TAG=1.0.0
   CONFIG_VOLUME=./studiKIS/standard-config
   ```

### 4. System starten
```bash
# Images herunterladen
docker compose pull

# Bahmni starten
docker compose up -d
```

### 5. Odoo 16 Berechtigungen fixen
Führen Sie diesen Befehl beim ersten Start aus, um den "Permission Denied" Fehler im Odoo-Filestore zu beheben:

```bash
docker compose exec -it --user root odoo chown -R odoo:odoo /var/lib/odoo/filestore && docker compose restart odoo
```

## 📖 Dokumentation
Detaillierte Anleitungen, Architekturübersichten und Hilfestellungen finden Sie in unserem Wiki:

**[Zum studiKIS Wiki](https://github.com/IMI-HD/studiKIS/wiki)**

Weitere Informationen zur Basis-Software finden Sie auf der [Bahmni Wiki Seite](https://bahmni.atlassian.net/wiki/).

## ⚖️ Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**. Siehe [LICENSE](./LICENSE) für Details.

---
