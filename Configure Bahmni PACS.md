# Bahmni Docker: Radiology Module Configuration & Troubleshooting Guide

This document summarizes the steps required to configure the Radiology Module in a Bahmni Docker environment (without Mirth Connect). It covers OpenMRS, the PACS Integration Service, and DCM4CHEE.

## Architecture Overview

1.  **OpenMRS:** Creates an order and publishes an event to the Atom Feed.
2.  **Atom Feed:** Acts as a queue (`/openmrs/ws/atomfeed/encounter/recent`).
3.  **PACS Integration Service:** Reads the feed, filters for Radiology orders, and converts them to HL7.
4.  **DCM4CHEE:** Receives the HL7 message and adds the patient to the Modality Worklist.

---

## 1. Monitoring Logs

To diagnose issues, you must check specific containers.

**1. PACS Integration Service (The Sender)**
This service reads from OpenMRS and sends to DCM4CHEE.
```bash
docker logs -f bahmni-standard-pacs-integration-1
```
*Note: If the queue is blocked or configuration is wrong, these logs might be silent regarding HL7 transfers.*

**2. DCM4CHEE (The Receiver)**
This is where successful HL7 messages appear.
```bash
docker logs -f bahmni-standard-dcm4chee-1
```

**Example of a successful HL7 log in DCM4CHEE:**
```text
11:11:34,632 INFO  [ServerImpl] handle - Socket[addr=/172.18.0.9,port=42368,localport=2575]
11:11:34,635 INFO  [HL7ServerService] Received HL7 message:
11:11:34,637 INFO  [HL7ServerService]
   MSH-4:BahmniEMR^BahmniEMR
   MSH-7:2025122911
   MSH-9:ORM^O01
   MSH-10:1767006694629173
   MSH-11:P
   MSH-12:2.5
   PID-3:ABC200018
   PID-5:^ABC200018
   PID-7:19991230000000+0000
   PID-8:M
   ORC-1:NW
   ORC-2:ORD-173
   ORC-3:ORD-173
   ORC-7:^^^^^ROUTINE
   ORC-10:^^BahmniEMR
   ORC-12:d7a67c17-5e07-11ef-8f7c-0242ac120002^^Super Man
   OBR-4:1234^abdomen ap
   OBR-39:^X-ray of abdomen, 2 views (AP supine and lateral decubitus)
   OBR-43:^Niklot,Stueber
```

---

## 2. OpenMRS Configuration (Source)

Bahmni requires specific global properties to be set in the OpenMRS database to communicate with the PACS server.

**Access the Database:**
```bash
sudo docker exec -it bahmni-standard-openmrsdb-1 bash
mysql -u'openmrs-user' -p'password' openmrs
```
*(Credentials are found in the `.env` file usually under `OPENMRS_DB_...`)*

**Required SQL Update:**
The `pacsquery.pacsConfig` property is often empty by default and cannot be set via the OpenMRS UI. It must be set via SQL to point to the internal Docker service name.

```sql
UPDATE global_property 
SET property_value = 'DCM4CHEE@dcm4chee:11112' 
WHERE property = 'pacsquery.pacsConfig';
```

**Verification:**
1.  Restart the OpenMRS container (`docker restart bahmni-standard-openmrs-1`).
2.  Check `https://localhost/openmrs/admin/maintenance/globalProps.form`.
3.  Search for search for ``pacsquery.pacsConfig``. If the variable is set to ``DCM4CHEE@dcm4chee:11112``, it worked. 
4.  Verify entries in the `event_records` table to ensure events are generating:
    ```sql
    SELECT * FROM event_records ORDER BY date_created DESC LIMIT 10;
    ```
---

## 3. PACS Integration Configuration (The Middleman)

The `pacs_integration_db` controls how the service reads the feed and where it sends data.

**Access the Database:**
```bash
sudo docker exec -it bahmni-standard-pacsdb-1 bash
psql -U pacs_integration_user -d pacs_integration_db
```
*(Credentials are found in the `.env` file under `PACS_INTEGRATION_DB_...`)*

### A. Fix the "Markers" Table
The service needs to know which Feed URI to listen to. It listens to the **Encounter** feed, not just the Radiology feed.

1.  **Get the current Feed state:**
    Run this on the host machine to find the latest feed ID (look for the `<id>` tag in the XML output):
    ```bash
    curl --insecure https://localhost/openmrs/ws/atomfeed/encounter/recent
    ```

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
    <title>Patient AOP</title>
    <link rel="self" type="application/atom+xml" href="http://localhost/openmrs/ws/atomfeed/encounter/recent" />
    <link rel="via" type="application/atom+xml" href="http://localhost/openmrs/ws/atomfeed/encounter/36" /> <!-- This is the 3rd Column-->
    <link rel="prev-archive" type="application/atom+xml" href="http://localhost/openmrs/ws/atomfeed/encounter/35" />
    <author>
        <name>OpenMRS</name>
    </author>
    <id>bec795b1-3d17-451d-b43e-a094019f6984+36</id>
    <generator uri="https://github.com/ICT4H/atomfeed">OpenMRS Feed Publisher</generator>
    <updated>2025-12-29T11:14:44Z</updated>
    <entry>
        <title>Encounter</title>
        <category term="Encounter" />
        <id>tag:atomfeed.ict4h.org:ffbd71d8-9fb6-49be-a6b3-3f085cce7e8c</id>
        <updated>2025-12-29T11:14:14Z</updated>
        <published>2025-12-29T11:14:14Z</published>
        <content type="application/vnd.atomfeed+xml"><![CDATA[/openmrs/ws/rest/v1/bahmnicore/bahmniencounter/e8be2e1e-d430-4fc1-845f-c4556efc061a?includeAll=true]]></content>
    </entry>
    <entry>
        <title>Encounter</title>
        <category term="Encounter" />
        <id>tag:atomfeed.ict4h.org:be4d353b-ac7b-4ee5-a5ac-1ca2f4b4d8e2</id> <!-- This is the 2rd Column - Take the most recent entry-->
        <updated>2025-12-29T11:14:44Z</updated>
        <published>2025-12-29T11:14:44Z</published>
        <content type="application/vnd.atomfeed+xml"><![CDATA[/openmrs/ws/rest/v1/bahmnicore/bahmniencounter/e8be2e1e-d430-4fc1-845f-c4556efc061a?includeAll=true]]></content>
    </entry>
    </feed>
    ```

2.  **Update the table:**
    Ensure the `markers` tables looks like this:
    ```sql
    SELECT * FROM markers;
    ```
    | feed_uri | last_read_entry_id | feed_uri_for_last_read_entry |
    | :--- | :--- | :--- |
    | `http://openmrs:8080/openmrs/ws/atomfeed/encounter/recent` | `tag:atomfeed.ict4h.org:be4d353b-ac7b-4ee5-a5ac-1ca2f4b4d8e2` | `http://openmrs:8080/openmrs/ws/atomfeed/encounter/36` |
    

### B. Fix the "Modality" Table
The target IP is often hardcoded to a specific IP (e.g., `192.168.33.10`) from legacy Vagrant setups. It must be changed to the Docker Service name.

```sql
SELECT * FROM modality;
```

| id | name | description | ip | port | timeout |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | DCM4CHEE | DCM4CHEE PACS | dcm4chee | 2575 | 3000 |

### C. Verify "Order Type"
Ensure the mapping exists.
```sql
SELECT * FROM order_type;
```
| id | name | modality_id |
| :--- | :--- | :--- |
| 1 | Radiology Order | 1 |

### D. The "Poisoned Queue" Fix (Critical)
If the system tried to process a malformed order (or a "Cancel" request for an order that doesn't exist), it will retry 7 times and then stop processing **all** subsequent orders. This blocks the queue completely.

**Solution:** Clear the failed events table.

```sql
DELETE FROM failed_events;
```

---

## 4. Known "Red Herrings" (Ignore these)

**Log Error:** `File not found /openmrs/data/bahmni_config/openmrs/observationsAdder/CurrentMonthOfTreatment.groovy`

* **Status:** Safe to ignore.
* **Context:** This error appears frequently in Bahmni logs but does not impact the Radiology order flow or HL7 generation. Do not waste time trying to fix this unless you specifically need that Groovy script functionality.

---

## 5. Metadata Import (OpenMRS Initializer)

It is currently in progress to automate the correct mapping of all radiology orders. Manual Mapping was done once along the Bahmni doku on this page: "https://bahmni.atlassian.net/wiki/spaces/BAH/pages/24969224/Map+PACS+procedure+codes"

---