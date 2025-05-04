# streamlit_app/app.py
import streamlit as st
import requests
import json
import time
import os 
import random # Import random module
import urllib.parse # Import urlencode
from dotenv import load_dotenv # Enable loading .env file

# --- Configuration & Environment --- 
# Load environment variables from .env file
load_dotenv()

# Agent API Configuration 
AGENT_API_BASE_URL = "http://localhost:8082" # Assumes port-forward is running
# Get API token from environment variable
AGENT_API_TOKEN = os.environ.get("AGENT_API_TOKEN")
if not AGENT_API_TOKEN:
    st.error("AGENT_API_TOKEN environment variable is not set. Please set it in the .env file.")
    st.stop()

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
default_name = "Joe Eyles"
default_title = "Vice Principal"
default_company = "Park Lane International School"
default_industry = "Education"
default_linkedin = "https://www.linkedin.com/in/joe-eyles-93b66b265"
default_product = "AI and DAta Platform for Education"

name = st.sidebar.text_input("Name", value=default_name)
title = st.sidebar.text_input("Title", value=default_title)
company = st.sidebar.text_input("Company", value=default_company)
industry = st.sidebar.text_input("Industry", value=default_industry)
linkedin_url = st.sidebar.text_input("LinkedIn URL", value=default_linkedin)
our_product = st.sidebar.text_area("Our Product/Service Description", value=default_product, height=100)

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
        result_area.info(f"Sending request to agent API at {AGENT_API_BASE_URL}...")
        
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
            "Authorization": f"Bearer {AGENT_API_TOKEN}"
        }

        run_id = None
        final_result_data = None
        error_message = None
        current_status = "starting"
        # polling_placeholder = result_area.empty() # We will use st.status instead

        try:
            # --- 1. Kick off the agent run --- 
            kickoff_url = f"{AGENT_API_BASE_URL}/kickoff"
            response = requests.post(kickoff_url, headers=headers, json=kickoff_payload, timeout=REQUEST_TIMEOUT) 
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            kickoff_data = response.json()
            run_id = kickoff_data.get('run_id')

            if not run_id:
                error_message = "Failed to get run_id from kickoff response."
                st.error(error_message)
                st.json(kickoff_data) # Show response if run_id is missing
            else:
                # result_area.info(f"Agent run kicked off. Run ID: {run_id}. Polling status...") # Remove initial info
                status_url = f"{AGENT_API_BASE_URL}/runs/{run_id}"

                # --- 2. Poll for status using st.status --- 
                start_time = time.time()
                last_funny_message = ""
                
                # Use st.status for dynamic updates
                with st.status(f"Kicked off Run ID: {run_id}. Waiting for agent...", expanded=True) as status_box:
                    while True:
                        # Check for overall timeout
                        if time.time() - start_time > POLLING_TIMEOUT_SECONDS:
                            error_message = f"Polling timed out after {POLLING_TIMEOUT_SECONDS} seconds."
                            current_status = "timeout"
                            status_box.update(label=error_message, state="error", expanded=True)
                            break
                            
                        try:
                            status_response = requests.get(status_url, headers=headers, timeout=REQUEST_TIMEOUT)
                            status_response.raise_for_status()
                            status_data = status_response.json()
                            current_status = status_data.get('status', 'unknown')
                            
                            # Update status box label 
                            elapsed_time = int(time.time() - start_time)
                            status_label = f"Run: {run_id} | Status: {current_status} | Elapsed: {elapsed_time}s"
                            
                            if current_status == 'completed':
                                final_result_data = status_data.get('result')
                                # --- Store result in session state before breaking --- 
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
                                             
                                    elif isinstance(final_result_data, dict) and all(k in final_result_data for k in ("subject_line", "email_body")):
                                        # Handle case where result is the direct dictionary
                                        st.session_state.generated_subject = final_result_data.get("subject_line")
                                        st.session_state.generated_body = final_result_data.get("email_body")
                                    else:
                                         error_message = "Completed, but result data is not in the expected format."
                                         current_status = "parsing_error"
                                         
                                except Exception as parse_e:
                                     error_message = f"Completed, but error parsing result: {parse_e}"
                                     current_status = "parsing_error"
                                     
                                status_box.update(label=f"Run {run_id} Completed!", state="complete", expanded=False)
                                break # Exit polling loop
                            elif current_status == 'error':
                                error_data = status_data.get('error', {'message': 'Unknown error occurred.'})
                                error_message = f"Agent run failed: {error_data.get('message', 'Details unavailable')}"
                                status_box.update(label=error_message, state="error", expanded=True)
                                # Also display the raw error JSON if available inside the box
                                try: 
                                    status_box.json(error_data)
                                except Exception as display_err: 
                                    status_box.write(f"Raw Error Data: {error_data} (JSON display failed: {display_err})")
                                break # Exit polling loop
                            elif current_status == 'processing':
                                # Update with a random funny message
                                last_funny_message = random.choice(FUNNY_STATUS_MESSAGES)
                                status_box.update(label=f"{last_funny_message} (Status: {current_status} | Elapsed: {elapsed_time}s)", state="running", expanded=True)
                                time.sleep(POLLING_INTERVAL_SECONDS) # Wait before next poll
                            else: # Handle unexpected statuses 
                                error_message = f"Unknown or unexpected run status received: {current_status}"
                                status_box.update(label=error_message, state="error", expanded=True)
                                status_box.json(status_data)
                                break # Exit polling loop

                        except requests.exceptions.RequestException as poll_err:
                            error_message = f"Error polling status for run {run_id}: {poll_err}"
                            current_status = "polling_error"
                            status_box.update(label=error_message, state="error", expanded=True)
                            break # Exit polling loop
                        except json.JSONDecodeError as json_err:
                             error_message = f"Error decoding status response for run {run_id}: {json_err}"
                             current_status = "polling_error"
                             status_box.update(label=error_message, state="error", expanded=True)
                             status_box.text(f"Raw response: {status_response.text}") # Show raw text if JSON fails
                             break
                        except Exception as loop_err:
                             # Catch any other unexpected error during polling
                             error_message = f"Unexpected error during polling loop: {loop_err}"
                             current_status = "polling_error"
                             status_box.update(label=error_message, state="error", expanded=True)
                             break

        except requests.exceptions.ConnectionError as conn_err:
            error_message = f"Connection Error: Could not connect to the agent API at {AGENT_API_BASE_URL}. Is the port-forward running? Error: {conn_err}"
            current_status = "connection_error"
        except requests.exceptions.Timeout as timeout_err:
             error_message = f"Request Timeout: The request to the agent API timed out. Error: {timeout_err}"
             current_status = "timeout_error"
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP Error: {http_err.response.status_code} {http_err.response.reason}. Response: {http_err.response.text}"
            current_status = "http_error"
        except Exception as e:
            error_message = f"An unexpected error occurred during kickoff or polling: {e}"
            current_status = "unknown_error"

        # --- 3. Display final result or error --- 
        # polling_placeholder.empty() # No longer used
        result_area.empty() # Clear initial info message
        
        # REMOVE redundant display logic from here. 
        # We rely on the display logic below based on session_state.
        
        # if current_status == 'completed' and st.session_state.generated_subject and st.session_state.generated_body:
        #    st.success(f"Run {run_id} completed successfully!")
            # ... NO LONGER DISPLAYING RESULT HERE ...
            
        # elif error_message:
        #    st.error(error_message) # Error is handled by the status box now
             
        # elif current_status not in ['completed', 'error', 'parsing_error']: 
        #     st.warning(f"Run {run_id or 'N/A'} did not complete successfully (final status: {current_status}).")

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