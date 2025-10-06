## Default Bahmni configuration and data for Bahmni Standard
======================================================================

This repository holds the Bahmni Configurations for Bahmni Standard with CIEL dictionary for metadata.

This repo has been forked from Bahmni/default-config and CIEL metadata is added on top of it.

Refer Bahmni Wiki for detailed explanation of each configuration: https://bahmni.atlassian.net/wiki/spaces/BAH/pages/2392073/Implementer+s+Guide

## Docker Image Build
The docker image bahmni/standard-config is generated using Github Actions. 

In order to build the image in local you can run the following command
```shell
docker build -t bahmni/standard-config -f package/docker/Dockerfile .
```

To dockerise your implementation specific config repository, follow the steps below:
1. Copy the package/docker directory to your repository
2. Add/ remove COPY statements in Dockerfile based on the needs.
3. Run the following command after updating image repository and image name.
    > docker build -t {repository}/{image-name} -f package/docker/Dockerfile .
4. Also you can add Github Actions from `.github/workflows` directory.

## How to use the config files to change the appearance of the website:
To change the bahmni website, you have to edit the corresponding JSON file located in the `standard-config > openmrs > apps`. Allmost all folders in the `apps` folder have an `apps.json` and an `extension.json` file, exept for the `customDisplayControl` and `dbNameCondition` folder. The folders `clinical`, `home`, `ipdDashboard`, `registration` and `reports` have addtional JSON files, containing configuurations specific for their sites. 

In general the names of these folders correspond to whatever name comes after `bahmni` in the URL (`localhost/bahmni/{folder_name}`). So if you want to make adjustments to the website, lookup the current URL and find the corresponing folder.

As soon as the changes are saved, you can reload the page and the changes should already be visible, no need to restart the docker container each time.

### Example 1: Changing the landing page on localhost
To change the landing page, you have to edit the file `whiteLabel.json` located in `standard-config > openmrs > apps > home`.

For example, if you want to change the welcome massage, you have to edit the following entry:
```json
"homePage": {
		"header_text": "<b>WELCOME TO<br />BAHMNI EMR & HOSPITAL SERVICE",
		"logo": "/bahmni_config/openmrs/apps/home/logo.png",
		"title_text": " "
        },
```

Or if you want to remove the "ANALYTICS" option from the six options below, you have to change the "enabled" variable to `false` 

```json
{
    "enabled": true,
    "name": "metabase",
    "title": "Analytics",
    "logo": "/bahmni/images/analytics.png",
    "link": "/metabase"
}
```

### Example 2: Editing the dashboard in the home folder
After selecting the "CLINICLA SERVICE" option on the homepage and loggin in, you are promted with 13 buttons labels "Registration" , "Programs", etc. . If you want to hide some of them, you have to edit the `extensions.json` file located in `standard-config > openmrs > apps > home`. However these JSON objects do not have an "enabled" variable, so in order to hide the elements on the webpage, you have to delete the entry, e.g. of the "AtomFeedConsole", if you do not want them to show up on the dashboard:
```json
  "atomfeedConsole": {
    "id": "bahmni.atomfeed.console",
    "extensionPointId": "org.bahmni.home.dashboard",
    "type": "link",
    "translationKey": "MODULE_LABEL_ATOMFEED_CONSOLE_KEY",
    "url": "/atomfeed-console",
    "icon": "fa fa-terminal",
    "order": 13,
    "requiredPrivilege": "app:admin"
  },
```