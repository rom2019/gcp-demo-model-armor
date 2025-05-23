import streamlit as st
import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, HarmCategory, HarmBlockThreshold, SafetySetting
from google.auth import default
from google.auth.transport.requests import Request
import requests
import json

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GCP Setting ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION")
MODEL_ARMOR_TEMPLATE_ID = os.getenv("MODEL_ARMOR_TEMPLATE_ID")

# Streamlit Setting
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT")) if os.getenv("STREAMLIT_SERVER_PORT") else None
STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS")

# --- Model Armor REST API  ---
def check_model_armor_rules(project_id: str, location: str, template_id: str, prompt_text: str):
    """
    Model Armor REST API를 사용하여 프롬프트 검사
    """
    try:
        # Auth
        credentials, _ = default()
        credentials.refresh(Request())
        
        # Model Armor API Endpoint
        endpoint = f"https://modelarmor.{location}.rep.googleapis.com/v1/projects/{project_id}/locations/{location}/templates/{template_id}:sanitizeUserPrompt"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        # API Request payload
        payload = {
            "user_prompt_data": {
                "text": prompt_text
            }
        }
        
        logger.info(f"Calling Model Armor REST API with template_id: {template_id}")
        logger.info(f"Endpoint: {endpoint}")
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Model Armor API Response: {result}")
            return parse_model_armor_response(result, prompt_text)
        else:
            logger.error(f"Model Armor API Error: {response.status_code} - {response.text}")
            return create_armor_error_result(f"API Error {response.status_code}: {response.text}", prompt_text)
            
    except Exception as e:
        logger.error(f"Error calling Model Armor API: {e}")
        return create_armor_error_result(str(e), prompt_text)

def parse_model_armor_response(response_data, prompt_text):
    """
    Model Armor API 응답 파싱 - 실제 응답 구조에 맞춤
    """
    armor_results = {
        "sensitive_data_protection": {"status": "No Match Found", "details": None},
        "prompt_injection_jailbreak": {"status": "No Match Found", "details": None},
        "malicious_urls": {"status": "No Match Found", "details": None},
        "responsible_ai": {
            "status": "No Match Found",
            "categories": {
                "Sexually Explicit": "No Match Found",
                "Hate Speech": "No Match Found",
                "Harassment": "No Match Found",
                "Dangerous": "No Match Found",
            }
        },
        "sanitized_prompt_request_raw": prompt_text,
        "issues_found": False,
        "prompt_blocked_by_safety": False,
        "llm_response_text": ""
    }
    
    try:
        violations_found = []
        
        # sanitizationResult 
        sanitization_result = response_data.get("sanitizationResult", {})
        filter_results = sanitization_result.get("filterResults", {})
        
        # overall match state check 
        overall_match_state = sanitization_result.get("filterMatchState", "")
        if overall_match_state == "MATCH_FOUND":
            armor_results["issues_found"] = True
            armor_results["prompt_blocked_by_safety"] = True
        
        # 1. Sensitive Data Protection (SDP)
        sdp_result = filter_results.get("sdp", {}).get("sdpFilterResult", {})
        sdp_match_state = sdp_result.get("inspectResult", {}).get("matchState", "")
        if sdp_match_state == "MATCH_FOUND":
            armor_results["sensitive_data_protection"]["status"] = "Violations found"
            violations_found.append("sensitive_data")
        
        # 2. Prompt Injection and Jailbreak
        pi_result = filter_results.get("pi_and_jailbreak", {}).get("piAndJailbreakFilterResult", {})
        pi_match_state = pi_result.get("matchState", "")
        if pi_match_state == "MATCH_FOUND":
            armor_results["prompt_injection_jailbreak"]["status"] = "Violations found"
            violations_found.append("prompt_injection")
        
        # 3. Malicious URLs
        malicious_uri_result = filter_results.get("malicious_uris", {}).get("maliciousUriFilterResult", {})
        malicious_uri_match_state = malicious_uri_result.get("matchState", "")
        if malicious_uri_match_state == "MATCH_FOUND":
            armor_results["malicious_urls"]["status"] = "Violations found"
            violations_found.append("malicious_urls")
        
        # 4. Responsible AI (RAI)
        rai_result = filter_results.get("rai", {}).get("raiFilterResult", {})
        rai_match_state = rai_result.get("matchState", "")
        rai_type_results = rai_result.get("raiFilterTypeResults", {})
        
        rai_violations_found = False
        
        # RAI Category Check
        if "harassment" in rai_type_results:
            harassment_result = rai_type_results["harassment"]
            if harassment_result.get("matchState") == "MATCH_FOUND":
                confidence = harassment_result.get("confidenceLevel", "Unknown")
                armor_results["responsible_ai"]["categories"]["Harassment"] = f"Violations found (Confidence: {confidence})"
                violations_found.append("harassment")
                rai_violations_found = True
        
        if "sexually_explicit" in rai_type_results:
            sexually_explicit_result = rai_type_results["sexually_explicit"]
            if sexually_explicit_result.get("matchState") == "MATCH_FOUND":
                confidence = sexually_explicit_result.get("confidenceLevel", "Unknown")
                armor_results["responsible_ai"]["categories"]["Sexually Explicit"] = f"Violations found (Confidence: {confidence})"
                violations_found.append("sexually_explicit")
                rai_violations_found = True
        
        if "hate_speech" in rai_type_results:
            hate_speech_result = rai_type_results["hate_speech"]
            if hate_speech_result.get("matchState") == "MATCH_FOUND":
                confidence = hate_speech_result.get("confidenceLevel", "Unknown")
                armor_results["responsible_ai"]["categories"]["Hate Speech"] = f"Violations found (Confidence: {confidence})"
                violations_found.append("hate_speech")
                rai_violations_found = True
        
        if "dangerous" in rai_type_results:
            dangerous_result = rai_type_results["dangerous"]
            if dangerous_result.get("matchState") == "MATCH_FOUND":
                confidence = dangerous_result.get("confidenceLevel", "Unknown")
                armor_results["responsible_ai"]["categories"]["Dangerous"] = f"Violations found (Confidence: {confidence})"
                violations_found.append("dangerous_content")
                rai_violations_found = True
        
        # RAI Overall Setting 
        if rai_violations_found:
            armor_results["responsible_ai"]["status"] = "Violations found"
            violations_found.append("rai")
        
        # Overall Setting 
        if violations_found:
            violation_list = " • ".join(violations_found)
            armor_results["overall_status"] = f"Violations found: • {violation_list}"
            armor_results["issues_found"] = True
            armor_results["prompt_blocked_by_safety"] = True
        else:
            armor_results["overall_status"] = "No violations found"
    
    except Exception as e:
        logger.error(f"Error parsing Model Armor response: {e}")
        logger.error(f"Response data: {response_data}")
        return create_armor_error_result(f"Response parsing error: {e}", prompt_text)
    
    return armor_results

def create_armor_error_result(error_message, prompt_text):
    """
    Error
    """
    return {
        "sensitive_data_protection": {"status": "API Error", "details": error_message},
        "prompt_injection_jailbreak": {"status": "API Error", "details": error_message},
        "malicious_urls": {"status": "API Error", "details": error_message},
        "responsible_ai": {
            "status": "API Error",
            "categories": {cat: "API Error" for cat in ["Sexually Explicit", "Hate Speech", "Harassment", "Dangerous"]},
        },
        "sanitized_prompt_request_raw": prompt_text,
        "issues_found": True,
        "prompt_blocked_by_safety": False,
        "llm_response_text": f"Model Armor API Error: {error_message}",
        "overall_status": f"API Error: {error_message}"
    }


def create_model_armor_template(project_id: str, location: str, template_id: str):
    """
    Model Armor Template 생성
    """
    try:
        credentials, _ = default()
        credentials.refresh(Request())
        
        endpoint = f"https://modelarmor.{location}.rep.googleapis.com/v1/projects/{project_id}/locations/{location}/templates"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "templateId": template_id,
            "template": {
                "displayName": f"Test Template {template_id}",
                "description": "Template for testing Model Armor integration"
            }
        }
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            logger.info(f"Template {template_id} created successfully")
            return True, "Template created successfully"
        else:
            logger.error(f"Template creation error: {response.status_code} - {response.text}")
            return False, f"Template creation failed: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return False, f"Template creation error: {e}"

def call_vertex_ai_with_model_armor(
    project_id: str,
    location: str,
    model_id: str,
    prompt_text: str,
    template_id: str,
    use_model_armor: bool = True
):

    
    if use_model_armor:
        logger.info("Checking prompt with Model Armor...")
        armor_results = check_model_armor_rules(project_id, location, template_id, prompt_text)
        
        if armor_results.get("prompt_blocked_by_safety", False):
            armor_results["llm_response_text"] = "Prompt blocked by Model Armor rules. LLM not called."
            return armor_results, None
    else:
        armor_results = {
            "sensitive_data_protection": {"status": "Not Checked", "details": None},
            "prompt_injection_jailbreak": {"status": "Not Checked", "details": None},
            "malicious_urls": {"status": "Not Checked", "details": None},
            "responsible_ai": {
                "status": "Not Checked",
                "categories": {
                    "Sexually Explicit": "Not Checked",
                    "Hate Speech": "Not Checked",
                    "Harassment": "Not Checked",
                    "Dangerous": "Not Checked",
                }
            },
            "sanitized_prompt_request_raw": prompt_text,
            "issues_found": False,
            "prompt_blocked_by_safety": False,
            "llm_response_text": "",
            "overall_status": "Model Armor not used"
        }
    
    try:
        vertexai.init(project=project_id, location=location)
        model = GenerativeModel(model_id)
        
        logger.info(f"Calling Vertex AI model {model_id} after Model Armor check...")
        response = model.generate_content(contents=[prompt_text])
        
        if response.candidates and response.candidates[0].content:
            llm_response_text = "".join(
                part.text for part in response.candidates[0].content.parts 
                if hasattr(part, 'text')
            )
            armor_results["llm_response_text"] = llm_response_text
        else:
            armor_results["llm_response_text"] = "No response generated from LLM."
        
        return armor_results, response
        
    except Exception as e:
        logger.error(f"Error calling Vertex AI: {e}")
        armor_results["llm_response_text"] = f"Vertex AI Error: {e}"
        return armor_results, None


def display_inspection_results_block(results_data):
    st.markdown("---")
    st.markdown("### 🛡️ Model Armor Inspection Results")
    

    overall_status = results_data.get("overall_status", "Unknown")
    if "Violations found" in overall_status:
        st.error(f"**Overall Status:** {overall_status} 🚨")
    elif "No violations" in overall_status:
        st.success(f"**Overall Status:** {overall_status} ✅")
    else:
        st.info(f"**Overall Status:** {overall_status} ℹ️")

    def display_status_line(label, status_info_dict, details_key="details"):
        status_text = status_info_dict.get("status", "N/A")
        icon = "✅" if "No Match Found" in status_text or "Not Checked" in status_text else "🚨"
        if "API Error" in status_text: icon = "⚠️"
        details_message = status_info_dict.get(details_key)
        details_string = f" ({details_message})" if details_message else ""
        st.markdown(f"**{label}:** {status_text} {icon}{details_string}")

    display_status_line("Sensitive Data Protection", results_data["sensitive_data_protection"])
    display_status_line("Prompt Injection and Jailbreak", results_data["prompt_injection_jailbreak"])
    display_status_line("Malicious URLs", results_data["malicious_urls"])

    rai_overall_status = results_data["responsible_ai"].get("status", "N/A")
    rai_icon = "✅" if "No Match Found" in rai_overall_status or "Not Checked" in rai_overall_status else "🚨"
    if "API Error" in rai_overall_status: rai_icon = "⚠️"
    st.markdown(f"**Responsible AI:** {rai_overall_status} {rai_icon}")

    if results_data["responsible_ai"].get("categories"):
        for category, cat_status in results_data["responsible_ai"]["categories"].items():
            cat_icon = "✅" if "No Match Found" in cat_status or "Not Checked" in cat_status else "🚨"
            if "API Error" in cat_status: cat_icon = "⚠️"
            st.markdown(f"  - **{category}:** {cat_status} {cat_icon}")

    with st.expander("Original Prompt"):
        st.text(results_data.get("sanitized_prompt_request_raw", "N/A"))
    st.markdown("---")


st.set_page_config(layout="wide", page_title="Model Armor + Vertex AI Demo")


st.sidebar.title("🛡️ Model Armor + Vertex AI Demo")

if not GCP_PROJECT_ID or not GCP_LOCATION:
    st.sidebar.error("GCP_PROJECT_ID and GCP_LOCATION environment variables must be set.")
    st.stop()
else:
    st.sidebar.success(f"Project: {GCP_PROJECT_ID}")
    st.sidebar.success(f"Location: {GCP_LOCATION}")
    st.sidebar.success(f"Model Armor Template: {MODEL_ARMOR_TEMPLATE_ID}")

with st.sidebar.expander("**Model Settings**", expanded=True):
    available_models = [
        "gemini-2.0-flash-001",
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
    model_selected_id = st.selectbox("Model", available_models, index=0)

with st.sidebar.expander("**Model Armor Settings**", expanded=True):
    use_model_armor = st.checkbox("Enable Model Armor Pre-check", value=True)
    template_id_input = st.text_input("Template ID", value=MODEL_ARMOR_TEMPLATE_ID)
    
    if use_model_armor:
        st.info("✅ Model Armor will check prompts before sending to LLM")
    else:
        st.warning("⚠️ Model Armor pre-check disabled")


with st.sidebar.expander("**API Information**", expanded=False):
    st.code(f"Endpoint: https://modelarmor.{GCP_LOCATION}.rep.googleapis.com/v1/projects/{GCP_PROJECT_ID}/locations/{GCP_LOCATION}/templates/{MODEL_ARMOR_TEMPLATE_ID}:sanitizeUserPrompt")
    st.info("Make sure Model Armor service is enabled:\n`gcloud services enable modelarmor.googleapis.com`")
    st.info("Correct payload format:\n```json\n{\n  \"user_prompt_data\": {\n    \"text\": \"your prompt here\"\n  }\n}\n```")


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Hello! I'm protected by Model Armor and powered by Vertex AI."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Ask anything (Model Armor will check first)..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.spinner("🛡️ Checking with Model Armor and calling Vertex AI..."):
        inspection_results, raw_response = call_vertex_ai_with_model_armor(
            project_id=GCP_PROJECT_ID,
            location=GCP_LOCATION,
            model_id=model_selected_id,
            prompt_text=user_prompt,
            template_id=template_id_input,
            use_model_armor=use_model_armor
        )

    display_inspection_results_block(inspection_results)

    llm_response_content = inspection_results.get("llm_response_text", "No response available.")
    
    if inspection_results.get("prompt_blocked_by_safety"):
        llm_response_content = "🚫 **Your prompt was blocked by Model Armor safety rules.** Please try rephrasing your request."

    with st.chat_message("assistant"):
        st.markdown(llm_response_content)
    st.session_state.messages.append({"role": "assistant", "content": llm_response_content})