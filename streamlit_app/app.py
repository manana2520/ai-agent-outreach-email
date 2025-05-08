# streamlit_app/app.py
import streamlit as st
import requests
import json
import time
import os 
import random # Import random module
import urllib.parse # Import urlencode
from dotenv import load_dotenv # Load environment variables from .env file
# from dotenv import load_dotenv # Not strictly needed for this version unless storing AGENT_API_TOKEN

# --- Configuration & Environment --- 
# Load environment variables
load_dotenv()

# --- Cloud URL (edit here if needed) ---
CLOUD_AGENT_API_BASE_URL = "https://sales-personalized-email-agent.agentic.canary-orion.keboola.dev"
LOCAL_AGENT_API_BASE_URL = "http://localhost:8082"

# --- Load both tokens from environment ---
AGENT_API_TOKEN = os.environ.get("AGENT_API_TOKEN")  # For local runner
CLOUD_AGENT_API_TOKEN = os.environ.get("CLOUD_AGENT_API_TOKEN")  # For cloud runner

POLLING_INTERVAL_SECONDS = 4 # Slightly longer interval for fun messages
REQUEST_TIMEOUT = 30 # Timeout for individual HTTP requests
POLLING_TIMEOUT_SECONDS = 360 # Overall timeout for waiting for the run to complete

# --- Funny Status Messages --- 
FUNNY_STATUS_MESSAGES = [
    "Recruiting agent from the digital ether...",
    "Agent woke up... needs coffee... ☕",
    "Briefing the new recruit (they seem confused)...",
    "Agent reading the manual (upside down)... 🤔",
    "Agent sharpening digital pencils...",
    "Running diagnostics... (mostly checking for rogue semicolons)",
    "Agent went for a virtual donut break... 🍩",
    "Untangling neural pathways... please hold...",
    "Consulting the digital ouija board...",
    "Polishing the crystal ball for insights... ✨",
    "Agent confirming task doesn't involve Clippy...📎",
    "Teaching the agent not to divide by zero...",
    "Negotiating with the API gods... 🙏",
    "Chasing rogue bits across the network...",
    "Waking up the AI hamster... 🐹",
    "Dusting off the algorithms...",
    "Searching for inspiration in the cloud(s)... ☁️",
    "Don't worry, the agent *usually* knows what it's doing...",
    "Performing arcane rituals for better results...",
    "Calculating the meaning of life (and your request)...",
]

# --- Streamlit App Layout --- 
st.set_page_config(layout="wide") # Use wider layout
st.title(" Personalized Sales Email Generator (Remote Agent Trigger)")
st.caption("UI for interacting with the deployed CrewAI agent via its API.")
st.warning(" Ensure the agent is deployed and the port-forward command is active in another terminal: `kubectl port-forward service/sales-personalized-email-agent -n ai-platform 8082:80`", icon="⚠️")

# --- Input Form --- 
st.sidebar.header("Prospect Details")
st.sidebar.caption("Enter the prospect information below.")

# Use default values from previous runs for convenience
default_name = "John Doe"
default_title = "CTO"
default_company = "Acme Corp"
default_industry = "Technology"
default_linkedin = "https://linkedin.com/in/johndoe"
default_product = "SuperCRM"

name = st.sidebar.text_input("Name", value=default_name)
title = st.sidebar.text_input("Title", value=default_title)
company = st.sidebar.text_input("Company", value=default_company)
industry = st.sidebar.text_input("Industry", value=default_industry)
linkedin_url = st.sidebar.text_input("LinkedIn URL", value=default_linkedin)
our_product = st.sidebar.text_area("Our Product/Service Description", value=default_product, height=100)

# --- Runner Mode and Agent Status (Semaphore) at Top of Sidebar ---
with st.sidebar:
    # Runner mode switch
    runner_mode = st.radio(
        "Choose where to run the agent:",
        ("Cloud runner", "Local runner"),
        index=0,
        help="Cloud runner calls the remote agent API. Local runner calls the local agentic runtime via HTTP."
    )
    # Dynamically set API base URL
    if runner_mode == "Cloud runner":
        AGENT_API_BASE_URL = CLOUD_AGENT_API_BASE_URL
    else:
        AGENT_API_BASE_URL = LOCAL_AGENT_API_BASE_URL

    # --- Always check status for the selected runner mode on every rerun ---
    # Cloud runner status
    cloud_status = "🔴 Cloud agent not responding"
    cloud_error = ""
    if not CLOUD_AGENT_API_TOKEN:
        cloud_error = "CLOUD_AGENT_API_TOKEN not set in environment."
    else:
        try:
            runs_url = f"{CLOUD_AGENT_API_BASE_URL}/runs?limit=1"
            headers = {"Authorization": f"Bearer {CLOUD_AGENT_API_TOKEN}"}
            resp = requests.get(runs_url, headers=headers, timeout=3)
            if resp.status_code == 200:
                _ = resp.json()
                cloud_status = "🟢 Cloud agent responding"
            else:
                cloud_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            cloud_error = str(e)
    # Local runner status
    local_status = "🔴 Local agent not responding"
    local_error = ""
    if not AGENT_API_TOKEN:
        local_error = "AGENT_API_TOKEN not set in environment."
    else:
        try:
            runs_url = f"{LOCAL_AGENT_API_BASE_URL}/runs?limit=1"
            headers = {"Authorization": f"Bearer {AGENT_API_TOKEN}"}
            resp = requests.get(runs_url, headers=headers, timeout=3)
            if resp.status_code == 200:
                _ = resp.json()
                local_status = "🟢 Local agent responding"
            else:
                local_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            local_error = str(e)
    # Display status for selected runner mode
    if runner_mode == "Cloud runner":
        st.write(cloud_status)
        # No error details shown
    else:
        st.write(local_status)
        # No error details shown

# Display area for results
result_area = st.container()

# Initialize session state 
if 'generated_subject' not in st.session_state:
    st.session_state.generated_subject = None
if 'generated_body' not in st.session_state:
    st.session_state.generated_body = None
if 'generate_button_clicked' not in st.session_state:
    st.session_state.generate_button_clicked = False # Track if generate was clicked this run

# --- Define Buttons Once --- 
# Define buttons here so their state is available throughout the script run
generate_clicked = st.sidebar.button("Generate Personalized Email", type="primary", key="generate_button")
clear_clicked = st.sidebar.button("Clear Results", key="clear_button")

# --- Handle Clear Button Action --- 
if clear_clicked:
     st.session_state.generated_subject = None
     st.session_state.generated_body = None
     st.session_state.generate_button_clicked = False # Reset generate flag too
     result_area.info("Results cleared. Fill in details and click generate.")
     # No rerun needed here, the rest of the script will handle the cleared state

# --- Agent Interaction (Triggered by Generate Button) --- 
if generate_clicked:
    st.session_state.generate_button_clicked = True # Flag that we started generation
    # Clear previous results from session state
    st.session_state.generated_subject = None
    st.session_state.generated_body = None
    
    # Validate inputs 
    if not all([name, title, company, industry, linkedin_url, our_product]):
        st.sidebar.error("Please fill in all prospect details.")
        # Reset flag if inputs are bad
        st.session_state.generate_button_clicked = False 
    else:
        result_area.empty() 
        # --- Unified agent call logic for both runners ---
        if runner_mode == "Cloud runner":
            api_base_url = CLOUD_AGENT_API_BASE_URL
            api_token = CLOUD_AGENT_API_TOKEN
        else:
            api_base_url = LOCAL_AGENT_API_BASE_URL
            api_token = AGENT_API_TOKEN
        result_area.info(f"Sending request to agent API at {api_base_url}...")
        inputs = {
            "name": name,
            "title": title,
            "company": company,
            "industry": industry,
            "linkedin_url": linkedin_url,
            "our_product": our_product,
        }
        kickoff_payload = {
            "crew": "sales_personalized_email", # Make sure this matches crew name if needed
            "inputs": inputs
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        run_id = None
        final_result_data = None
        error_message = None
        current_status = "starting"
        try:
            kickoff_url = f"{api_base_url}/kickoff"
            response = requests.post(kickoff_url, headers=headers, json=kickoff_payload, timeout=REQUEST_TIMEOUT) 
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            kickoff_data = response.json()
            run_id = kickoff_data.get('run_id')
            if not run_id:
                error_message = "Failed to get run_id from kickoff response."
                st.error(error_message)
                st.json(kickoff_data) # Show response if run_id is missing
            else:
                status_url = f"{api_base_url}/runs/{run_id}"
                status_label = f"Run: {run_id} | Status: {current_status} | Elapsed: 0s"
                # --- 2. Poll for status using a custom container for two-line display ---
                status_container = st.empty()
                start_time = time.time()
                last_funny_message = ""
                while True:
                    if time.time() - start_time > POLLING_TIMEOUT_SECONDS:
                        error_message = f"Polling timed out after {POLLING_TIMEOUT_SECONDS} seconds."
                        current_status = "timeout"
                        status_container.markdown(f"**{status_label}**  \n:warning: {error_message}")
                        break
                    try:
                        status_response = requests.get(status_url, headers=headers, timeout=REQUEST_TIMEOUT)
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        current_status = status_data.get('status', 'unknown')
                        elapsed_time = int(time.time() - start_time)
                        status_label = f"Run: {run_id} | Status: {current_status} | Elapsed: {elapsed_time}s"
                        if current_status == 'completed':
                            final_result_data = status_data.get('result')
                            try:
                                if isinstance(final_result_data, dict) and 'content' in final_result_data:
                                    content_data = final_result_data['content']
                                    if isinstance(content_data, str):
                                        parsed_email_data = json.loads(content_data)
                                    elif isinstance(content_data, dict):
                                        parsed_email_data = content_data
                                    else: 
                                        raise ValueError("Content is not a string or dictionary")
                                    if parsed_email_data and isinstance(parsed_email_data, dict):
                                         st.session_state.generated_subject = parsed_email_data.get("subject_line")
                                         st.session_state.generated_body = parsed_email_data.get("email_body")
                                    else:
                                         error_message = "Completed, but failed to parse email data structure from result content."
                                         current_status = "parsing_error"
                            except Exception as e:
                                error_message = f"Error parsing result: {e}"
                                current_status = "parsing_error"
                            status_container.markdown(f"**{status_label}**  \n:heavy_check_mark: Completed!")
                            break
                        elif current_status == 'error':
                            error_message = status_data.get('error', {}).get('message', 'Unknown error')
                            status_container.markdown(f"**{status_label}**  \n:warning: Run failed: {error_message}")
                            break
                        else:
                            # Show a random funny message, always on a new line under the status
                            funny_message = random.choice(FUNNY_STATUS_MESSAGES)
                            if funny_message != last_funny_message:
                                status_container.markdown(f"**{status_label}**  \n{funny_message}")
                                last_funny_message = funny_message
                            time.sleep(POLLING_INTERVAL_SECONDS)
                    except Exception as e:
                        error_message = f"Error polling run status: {e}"
                        status_container.markdown(f"**{status_label}**  \n:warning: {error_message}")
                        break
        except Exception as e:
            error_message = f"Error during agent API call: {e}"
            st.error(error_message)

# --- Display Area Logic (Runs on every interaction) --- 
# This section now handles all result display based on session_state

# Clear initial info message if we have a result or if generate was just clicked
if st.session_state.generated_subject or st.session_state.generate_button_clicked:
     result_area.empty()
else: 
     # Show initial message only if no result and generate wasn't clicked
     result_area.info("Fill in the prospect details in the sidebar and click 'Generate Personalized Email' to start.")

if st.session_state.generated_subject and st.session_state.generated_body:
    st.success("Email Generated Successfully!") 
    st.subheader("Subject:")
    st.write(st.session_state.generated_subject)
    
    st.subheader("Body:")
    email_body_display = st.session_state.generated_body.replace('\\n', '\n')
    st.text_area("Generated Email Body", email_body_display, height=400, key="email_body_display_persistent") 
    
    # --- Add Gmail Compose Link --- 
    st.divider()
    try:
        subject_encoded = urllib.parse.quote_plus(st.session_state.generated_subject)
        body_for_link = st.session_state.generated_body.replace('\\n', '\n') 
        body_encoded = urllib.parse.quote_plus(body_for_link)
        # Construct Gmail URL instead of mailto:
        gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&su={subject_encoded}&body={body_encoded}"
        
        # Keep using st.link_button
        st.link_button("Compose in Gmail", gmail_link, type="primary")
        st.caption("(Opens Gmail compose window with subject and body. Requires login.)")
    except Exception as link_e:
        st.error(f"Could not generate 'Compose in Gmail' link: {link_e}")

# Reset generate button flag after the script run completes
st.session_state.generate_button_clicked = False 