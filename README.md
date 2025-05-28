# Model Armor + Vertex AI Demo

This project demonstrates the integration of Model Armor with Google Cloud Vertex AI to provide enhanced safety and security for generative AI applications. It features a Streamlit-based chat interface that uses Model Armor to inspect user prompts before sending them to a Vertex AI generative model.

## Features

*   **Interactive Chat Interface:** Allows users to interact with a Vertex AI generative model.
*   **Model Armor Integration:** User prompts are inspected by Model Armor before being processed by the Vertex AI model.
*   **Safety Inspection Results:** The application displays detailed results from Model Armor, including checks for:
    *   Sensitive Data Protection (SDP)
    *   Prompt Injection and Jailbreak attempts
    *   Malicious URLs
    *   Responsible AI (RAI) categories (e.g., Harassment, Hate Speech, Sexually Explicit, Dangerous)
*   **Configurable:** Users can configure the Vertex AI model and the Model Armor Template ID.

## Technologies Used

*   **Python:** The core programming language for the application.
*   **Streamlit:** Used to create the interactive web-based chat interface.
*   **Google Cloud Vertex AI:** Provides the generative AI models.
*   **Model Armor:** A Google Cloud service used to inspect and sanitize user prompts for safety.
*   **Docker:** Used to containerize the application for deployment.
*   **Google Cloud Run:** Used to deploy and serve the containerized application.
*   **Google Auth & API Client Libraries:** For authenticating and interacting with Google Cloud services.

## Setup and Deployment

### Prerequisites

1.  **Google Cloud Project:** You'll need an active Google Cloud Project.
2.  **`gcloud` CLI:** Ensure the Google Cloud CLI is installed and authenticated. You can find installation instructions [here](https://cloud.google.com/sdk/docs/install).
3.  **Enable APIs:** The following Google Cloud APIs must be enabled in your project:
    *   Cloud Run API (`run.googleapis.com`)
    *   Cloud Build API (`cloudbuild.googleapis.com`)
    *   Vertex AI API (`aiplatform.googleapis.com`)
    *   Model Armor API (`modelarmor.googleapis.com`)
    You can enable these using the `gcloud services enable` command (as shown in the `deploy.sh` script) or via the Google Cloud Console.

### Deployment Steps

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory>
    ```
2.  **Configure Deployment Script:**
    Open the `deploy.sh` file and update the following environment variables with your specific settings:
    *   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
    *   `GCP_LOCATION`: The Google Cloud region where you want to deploy the service (e.g., `us-central1`).
    *   `MODEL_ARMOR_TEMPLATE_ID`: The ID of your Model Armor template.
        *   **Note on Model Armor Template:** If you don't have an existing Model Armor template, you might need to create one. The application (`app.py`) includes a function `create_model_armor_template` which can be adapted or used as a reference. Alternatively, you can create and manage templates via the Model Armor API or console if available. Ensure the template ID used here is valid and accessible in your project and region. The `deploy.sh` script currently sets a default `MODEL_ARMOR_TEMPLATE_ID="model-armor-demo"`.

3.  **Run the Deployment Script:**
    Make the script executable and run it:
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```
    This script will build the Docker image, push it to Google Container Registry (or Artifact Registry, depending on project settings), and deploy the service to Cloud Run.

## Running the Application

Once the `deploy.sh` script completes successfully, it will output the **Service URL**. Open this URL in your web browser to access the application.

The application presents a chat interface. You can:

1.  **Enter a prompt** in the input field at the bottom of the chat.
2.  The application will first send the prompt to **Model Armor** for inspection (if enabled in the sidebar).
3.  The **Model Armor Inspection Results** will be displayed, showing any detected violations or if the prompt is considered safe.
4.  If the prompt is not blocked by Model Armor, it will then be sent to the configured **Vertex AI generative model**.
5.  The **model's response** will appear in the chat.

You can adjust settings in the sidebar:
*   **Model Settings:** Choose different Vertex AI models.
*   **Model Armor Settings:** Enable/disable Model Armor pre-checks and specify the Template ID.

## Environment Variables

The application utilizes the following environment variables, which are primarily set during the Cloud Run deployment via the `deploy.sh` script:

*   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
*   `GCP_LOCATION`: The Google Cloud region for deployment and services.
*   `MODEL_ARMOR_TEMPLATE_ID`: The identifier for the Model Armor template to be used for prompt inspection.

The `Dockerfile` also defines other environment variables like `STREAMLIT_SERVER_PORT`, `STREAMLIT_SERVER_ADDRESS`, `STREAMLIT_SERVER_HEADLESS`, and `STREAMLIT_BROWSER_GATHER_USAGE_STATS`. These are generally pre-configured for running Streamlit applications in a containerized environment like Cloud Run and typically do not require modification for standard deployment.

## How Model Armor Integration Works

The core logic for integrating Model Armor is found in `app.py`. The typical flow is as follows:

1.  **User Input:** The user enters a prompt into the Streamlit chat interface.
2.  **Model Armor Pre-Check (if enabled):**
    *   The `call_vertex_ai_with_model_armor` function is invoked.
    *   If Model Armor is enabled, this function first calls `check_model_armor_rules`.
    *   `check_model_armor_rules` makes a REST API call to the Model Armor service endpoint (`https://modelarmor.<location>.rep.googleapis.com/.../:sanitizeUserPrompt`) with the user's prompt and the configured `MODEL_ARMOR_TEMPLATE_ID`.
    *   Model Armor inspects the prompt based on the rules defined in the template.
3.  **Safety Decision:**
    *   The `parse_model_armor_response` function processes the JSON response from Model Armor.
    *   If Model Armor flags the prompt as violating safety policies (e.g., detects sensitive data, prompt injection, etc.), the prompt might be blocked (`prompt_blocked_by_safety`).
4.  **Vertex AI Call (if not blocked):**
    *   If the prompt is not blocked by Model Armor (or if Model Armor is disabled), the `call_vertex_ai_with_model_armor` function proceeds to call the selected Vertex AI generative model (`gemini-2.0-flash-001`, `gemini-1.5-pro`, etc.) with the original prompt.
5.  **Display Results:**
    *   The application displays:
        *   The Model Armor inspection results (via `display_inspection_results_block`).
        *   The response from the Vertex AI model (if called). If the prompt was blocked, a message indicating this is shown instead.

This pre-check mechanism helps ensure that potentially harmful or unwanted prompts are evaluated and optionally blocked before they reach the generative model, adding a layer of security and control.
