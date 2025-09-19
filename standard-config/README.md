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
