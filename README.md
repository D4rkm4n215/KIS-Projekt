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

Dieses Repository enthält die Konfiguration, die mit den offiziellen Bahmni-Docker-Containern genutzt wird.

1.  **Repository klonen:**
    ```bash
    git clone [https://github.com/IMI-HD/studiKIS.git](https://github.com/IMI-HD/studiKIS.git)
    cd studiKIS
    ```

2.  **Bahmni Docker Setup vorbereiten:**
    Nutzen Sie das offizielle [Bahmni Docker Repository](https://github.com/Bahmni/bahmni-docker) oder Ihre bestehende `docker-compose.yml`.

3.  **Config-Pfad anpassen:**
    Um die studiKIS-Konfiguration zu laden, muss der Pfad im `docker-compose.yml` File unter dem Service `bahmni-standard-config` (oder dem entsprechenden Web-Container) auf das lokale Verzeichnis gemappt werden:

    ```yaml
    services:
      bahmni-web:
        volumes:
          - ./standard-config:/var/www/bahmni_config:ro
    ```
    *(Hinweis: Der genaue Pfad kann je nach genutzter Bahmni-Version und Compose-Struktur leicht variieren.)*

4.  **Container starten:**
    ```bash
    docker-compose up -d
    ```

## 📖 Dokumentation
Detaillierte Anleitungen, Architekturübersichten und Hilfestellungen finden Sie in unserem Wiki:

**[Zum studiKIS Wiki](https://github.com/IMI-HD/studiKIS/wiki)**

Weitere Informationen zur Basis-Software finden Sie auf der [Bahmni Wiki Seite](https://bahmni.atlassian.net/wiki/).

## ⚖️ Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**. Siehe [LICENSE](./LICENSE) für Details.

---
