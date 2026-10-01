import os
import hmac
import hashlib
import json
from flask import Blueprint, request, abort, current_app, redirect, render_template, session, url_for

bp = Blueprint("github", __name__)
GITHUB_SECRET = os.environ.get("GITHUB_SECRET", "").encode()

def verify_signature(payload, signature):
    """Verify that the payload matches the GitHub signature."""
    if not signature:
        return False
    # GitHub signatures look like 'sha256=xxxx...'
    sha_name, signature_hex = signature.split('=')
    if sha_name != 'sha256':
        return False
    
    # Calculate local signature
    mac = hmac.new(GITHUB_SECRET, msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature_hex)

def handle_push_event(payload):
    ref = payload.get('ref')  # e.g., 'refs/heads/main'
    repo_name = payload.get('repository', {}).get('full_name')
    print(f"Code pushed to {ref} in {repo_name}")
    

@bp.route('/webhook', methods=['POST'])
def receive_github_webhook():
    # 1. Get the signature from headers
    signature = request.headers.get('X-Hub-Signature-256')
    
    # 2. Verify the payload authenticity
    if not verify_signature(request.data, signature):
        abort(403, "Invalid signature")

    # 3. Read the type of GitHub event (e.g., 'push', 'pull_request')
    event_type = request.headers.get('X-GitHub-Event')

    # 4. Extract data from the payload
    payload = request.json
    
    # Example parsing for a push event
    if event_type == 'push':
        handle_push_event(payload)
        
    return json.dumps({'success': True}), 200
