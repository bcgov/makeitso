import os
import hmac
import hashlib
import json
from flask import Blueprint, request, abort

bp = Blueprint("github", __name__)
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode()

def verify_signature(payload, signature):
    """Verify that the payload matches the GitHub signature."""
    if not signature:
        return False
    sha_name, signature_hex = signature.split('=')
    if sha_name != 'sha256':
        return False
    
    # Calculate local signature
    mac = hmac.new(GITHUB_WEBHOOK_SECRET, msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature_hex)

def handle_push_event(payload):
    ref = payload.get('ref')  # e.g., 'refs/heads/main'
    repo_name = payload.get('repository', {}).get('full_name')
    print(f"Code pushed to {ref} in {repo_name}")
    

@bp.route('/webhook', methods=['POST'])
def receive_github_webhook():
    # Get the signature from headers
    signature = request.headers.get('X-Hub-Signature-256')
    # Verify the payload authenticity
    if not verify_signature(request.data, signature):
        abort(403, "Invalid signature")
    # Read the type of GitHub event (e.g., 'push', 'pull_request')
    event_type = request.headers.get('X-GitHub-Event')
    # Extract data from the payload
    payload = request.json

    # Handle Push Events
    if event_type == 'push':
        handle_push_event(payload)
        
    return json.dumps({'success': True}), 200
