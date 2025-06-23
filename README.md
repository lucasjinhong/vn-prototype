# Visual Novel Engine - CI/CD Pipeline

This project is a scalable, web visual novel engine designed to be fully localizable and content-driven, allowing authors to write stories, create dynamic questions, and manage assets in simple YAML files without touching the core application code.

The entire application is containerized with **Docker**, orchestrated with **Kubernetes (GKE)**, and the cloud infrastructure is managed declaratively with **Terraform** and deployed automatically with **GitHub Actions**.

# Demo Website

http://34.81.249.188

## Features

*   **Dynamic Storytelling:** Story flow driven by simple YAML files.
*   **Localization Support:** Architected for multiple languages (`en-US`, `zh-TW`, etc.).
*   **Interactive Questions:** Supports both static and dynamic (Python-generated) questions.
*   **Professional DevOps Workflow:**
    *   **Local Development:** Run a lightweight version with Flask's development server.
    *   **Containerization:** Packaged with **Docker**.
    *   **Infrastructure as Code (IaC):** GCP resources managed by **Terraform**.
    *   **Orchestration:** Deployed on **Google Kubernetes Engine (GKE)**.
    *   **CI/CD Automation:** Automated build, push, and deployment pipeline using **GitHub Actions**.

---

## 1. Local Development Setup

For quickly testing code and content changes on your local machine.

### Prerequisites
*   Python 3.9+

### Setup Steps
1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the development server:**
    ```bash
    python3 src/run.py
    ```
3.  **Access the application** at `http://localhost:5000`.

---

## 2. GCP Deployment with Terraform and Kubernetes

This workflow deploys the entire application stack to Google Cloud Platform.

### Prerequisites
*   **Google Cloud SDK (`gcloud`)** installed and authenticated (`gcloud auth login`).
*   **Terraform** installed.
*   **Docker** installed.
*   **kubectl** installed.
*   A free tier GCP account or GCP project with billing enabled.
*   **APIs Enabled:** Ensure `compute.googleapis.com`, `container.googleapis.com`, and `artifactregistry.googleapis.com` are enabled in your GCP project.

### Step 2.1: Configure Terraform Variables

Before deploying, you must configure your GCP settings. Create a file named `terraform.tfvars` inside the `terraform/` directory. **This file should not be committed to version control.**

**Create `terraform/terraform.tfvars` with the following content:**
```tfvars
# terraform/terraform.tfvars

gcp_project_id = "your-gcp-project-id"
gcp_region     = "asia-east1" # e.g., us-central1, us-east1, us-east1
app_name       = "vn-prototype"
```
*   Replace `"your-gcp-project-id"` with your actual GCP Project ID.
*   You can change the region and zone if you wish.

### Step 2.2: Provision Infrastructure with Terraform

1.  **Navigate to the Terraform directory:**
    ```bash
    cd vn-prototype-project/terraform
    ```
2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```
3.  **Apply the configuration:**
    Terraform will automatically use the values from your `terraform.tfvars` file. Type `yes` when prompted.
    ```bash
    terraform apply
    ```
    This may take 5-10 minutes.

### Step 2.3: Manual Deployment (First Time)

Follow these steps for the initial deployment or for manual updates. For automated updates, see the GitHub Actions section.

1.  **Configure Docker & kubectl for GCP:**
    ```bash
    # Replace with your values from terraform.tfvars
    GCP_PROJECT_ID="your-gcp-project-id"
    GCP_REGION="asia-east1"

    gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
    gcloud container clusters get-credentials vn-prototype-gke-cluster --region ${GCP_REGION} --project ${GCP_PROJECT_ID}
    ```

2.  **Create a Cluster Static IP(for someone without a domain)**
    ```bash
    gcloud compute addresses create vn-prototype-static-ip \
        --project=${GCP_PROJECT_ID} \
        --region=asia-east1
    ```

3.  **Get the IP Address**
    ```bash
    gcloud compute addresses describe vn-prototype-static-ip \
        --region=asia-east1 \
        --format="value(address)"
    ```

4.  **Paste the IP Address to kubernetes/service.yaml**
    ```yaml
    loadBalancerIP: xxx.xxx.xxx.xxx # <-- PASTE YOUR RESERVED IP HERE
    ```

5.  **Build and Push the Docker Image:**
    ```bash
    cd ../src # Navigate to the src directory

    IMAGE_TAG="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/vn-prototype-repo/vn-prototype:v1.0"
    echo ${IMAGE_TAG} # Remember this for apply to kubernetes/app-deployment.yaml
    docker build -t ${IMAGE_TAG} .
    docker push ${IMAGE_TAG}
    ```

6.  **Update and Apply Kubernetes Deployment and Service:**
    *   Open `kubernetes/app-deployment.yaml`.
    *   Change the `image:` line to the full `${IMAGE_TAG}` you just created.
    *   Apply the manifest:
        ```bash
        kubectl apply -f ../kubernetes/app-deployment.yaml
        kubectl apply -f ../kubernetes/service.yaml
        ```

7.  **Access the Application:**
    ```bash
    kubectl get service vn-prototype-service -w
    ```
    Wait for the `EXTERNAL-IP` to be assigned, then access it via `http://<EXTERNAL_IP>`.

---

## 3. Automated CI/CD with GitHub Actions

This pipeline automatically builds, pushes, and deploys your application to GKE whenever you push changes to the `main` branch.

### Step 3.1: GitHub Repository Setup

1.  **Create a GCP Service Account:** This gives GitHub Actions permission to access your GCP project.
    ```bash
    # Set environment variables
    export GCP_PROJECT_ID="your-gcp-project-id"
    export SA_NAME="github-actions-deployer"
    export GITHUB_ORG="lucasjinhong"
    export GITHUB_REPO="your-repo-name"

    # 1. Create the Service Account
    gcloud iam service-accounts create $SA_NAME \
      --project="${GCP_PROJECT_ID}" \
      --display-name="GitHub Actions Deployer"

    # 2. Create a Workload Identity Pool
    gcloud iam workload-identity-pools create "github" \
      --project="${GCP_PROJECT_ID}" \
      --location="global" \
      --display-name="GitHub Actions Pool"

    # 3. Get the full ID of the pool
    export WORKLOAD_POOL_ID=$(gcloud iam workload-identity-pools describe "github" --project="${GCP_PROJECT_ID}" --location="global" --format="value(name)")

    # 4. Create a Workload Identity Provider for your GitHub repo
    gcloud iam workload-identity-pools providers create-oidc "my-repo-provider" \
      --project="${GCP_PROJECT_ID}" \
      --location="global" \
      --workload-identity-pool="github" \
      --display-name="My GitHub repo provider" \
      --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
      --attribute-condition="assertion.repository_owner == '${GITHUB_ORG}'" \
      --issuer-uri="https://token.actions.githubusercontent.com"

    # 5. Grant necessary permissions to the GCP Service Account
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member="serviceAccount:$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/container.developer"
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member="serviceAccount:$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/artifactregistry.writer"

    # 6. Allow the GitHub Actions identity to impersonate the GCP Service Account (The final binding)
    gcloud iam service-accounts add-iam-policy-binding "$SA_NAME@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --project="${GCP_PROJECT_ID}" \
      --role="roles/iam.workloadIdentityUser" \
      --member="principalSet://iam.googleapis.com/${WORKLOAD_POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
    ```

2.  **Add Secrets to Your GitHub Repository:**
    *   Go to your repository on GitHub > Settings > Secrets and variables > Actions.
    *   Click "New repository secret" and add the following:
        *   **`GCP_PROJECT_ID`**: Your Google Cloud Project ID.
        *   **`GCP_SA_EMAIL`**: The email of the service account you just created (`github-actions-deployer@your-gcp-project-id.iam.gserviceaccount.com`).
        *   **`GCP_WORKLOAD_IDENTITY_PROVIDER`**: The full path of the provider. You can get it by running:
            ```bash
            gcloud iam workload-identity-pools providers describe "my-repo-provider" \
              --project="${GCP_PROJECT_ID}" \
              --location="global" \
              --workload-identity-pool="github" \
              --format="value(name)"
            ```

### Step 3.2: Create the GitHub Actions Workflow File

Create the file `.github/workflows/xxx.yml` in your project root with the following content.

| Workflow | Status |
| :--- | :--- |
| **Infrastructure (Terraform)** | [![Terraform Infrastructure CI/CD](https://github.com/lucasjinhong/vn-prototype/actions/workflows/terraform.yaml/badge.svg)](https://github.com/lucasjinhong/vn-prototype/actions/workflows/terraform.yaml) |
| **Release Artifact Creation** | [![Create Release Artifact](https://github.com/lucasjinhong/vn-prototype/actions/workflows/release.yaml/badge.svg)](https://github.com/lucasjinhong/vn-prototype/actions/workflows/release.yaml) |
| **Deployment to GKE** | [![Deploy to GKE](https://github.com/lucasjinhong/vn-prototype/actions/workflows/deploy.yaml/badge.svg)](https://github.com/lucasjinhong/vn-prototype/actions/workflows/deploy.yaml) |

### Step 3.3: Trigger the Workflow
Commit and push all your files, including the new `.github/workflows/xxx.yml` file, to the `main` branch of your GitHub repository. Go to the "Actions" tab on GitHub to watch your pipeline run automatically.

---

## 4. Cleaning Up

To avoid ongoing costs, you can destroy all the GCP resources created by Terraform.

1.  **Navigate to the Terraform directory:**
    ```bash
    cd vn-prototype-project/terraform
    ```
2.  **Run the destroy command:**
    ```bash
    terraform destroy
    ```