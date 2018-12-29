# MT Photo Analysis Cloud Function

[![Build Status](https://travis-ci.org/MirosTruckstop/mt-photo-analysis-function.svg?branch=master)](https://travis-ci.org/MirosTruckstop/mt-photo-analysis-function)

## Setup

### Local setup

Requirements
* Python 3.7+ is installed
* virtualenv is installed

Install the dependencies

1. Create a virtual environment: `virtualenv --python python3.7 env`
2. Activate virtual environment: `source ./env/bin/activate`
3. Install the dependencies: `pip install -r requirements.txt`

### Google Cloud Platform project setup

Requirements
* A Google Cloud Platform project exists
* gcloud is installed and initialised

1. Enable the required APIs
    ```sh
    gcloud services enable pubsub.googleapis.com
    gcloud services enable cloudfunctions.googleapis.com
    gcloud services enable vision.googleapis.com
    ```

2. Create a service account
    ```sh
    gcloud iam service-accounts create photo-analysis-function --display-name "photo-analysis-function"
    ```

3. Create a Cloud Pub/Sub Topic: `gcloud pubsub topics create photo-analysis-request`

4. (Create a Firestore collection named `photos`)

### Deploy

Deploy the Cloud Function.
```sh
GCP_PROJECT=YOUR-PROJECT-ID
WP_HOST=https://YOUR-HOST.ORG
GCP_REGION=europe-west1
GCP_TOPIC=photo-analysis-request
# 'beta' is required to set the service account
gcloud --project ${GCP_PROJECT} beta functions deploy photo_analysis \
    --runtime python37 \
    --trigger-topic ${GCP_TOPIC} \
    --region ${GCP_REGION} \
    --set-env-vars WP_HOST=${WP_HOST},WP_JWT=${JWT} \
    --service-account photo-analysis-function@${GCP_PROJECT}.iam.gserviceaccount.com
```
