import json
import os
import requests
import subprocess
from dotenv import load_dotenv

# 1. Securely load your Groq API key from the .env file
load_dotenv()
api_key = os.getenv("AI_API_KEY")

def extract_wazuh_alerts(file_path):
    logs = []
    with open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    print("Skipping invalid JSON line.")
    return logs

def analyze_alert_with_ai(alert):
    # 2. Connect to Groq's API
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 3. The industry-standard prompt instructing the AI how to triage the alert
    prompt = (
        "You are an experienced tier 1 SOC analyst. Review the SIEM alerts and decide which alerts are "
        "interesting or not-interesting. An interesting alert indicates a potential incident that needs "
        "to be investigated further. A non-interesting alert is either informational or a false positive. "
        "Make this decision based on the details in the alert.\n\n"
        f"Alert details: {json.dumps(alert)}\n\n"
        "Your message should use the following format:\n"
        "alert_id:\nalert_description:\nalert_decision:\nreason:"
    )

    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "user", "content": prompt}]
    }

    print("Sending alert to the AI Analyst for review...")
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("\n=== AI SOC Analyst Decision ===")
        # FIXED: Explicitly added  to extract the text from the choices array
        print(result['choices']['message']['content'].strip())
        print("===============================\n")
    else:
        print(f"Error connecting to AI: {response.status_code} - {response.text}")

# Extract the alerts from our local file
extracted_alerts = extract_wazuh_alerts('/var/ossec/logs/alerts/alerts.json')

print(f"Successfully extracted {len(extracted_alerts)} alerts ready for AI triage!")

# Send the first alert to the AI for analysis
if extracted_alerts:
    # FIXED: Added  to send just the single alert from the list
    analyze_alert_with_ai(extracted_alerts)
      
# === AUTOMATE GITHUB PUSH ===
def push_to_github():
    print("Saving daily AI triage report to GitHub...")
    try:
        # Tell Git to track the updated files
        subprocess.run(["git", "add", "."], check=True)
        # Commit the changes with a message
        subprocess.run(["git", "commit", "-m", "Automated Daily AI Triage Report"], check=True)
        # Push to the remote repository
        subprocess.run(["git", "push"], check=True)
        print("Successfully updated your GitHub portfolio!")
    except subprocess.CalledProcessError as e:
        print(f"Error syncing with GitHub. Did you make any new changes to commit? Details: {e}")

# Run the automated push
push_to_github()
