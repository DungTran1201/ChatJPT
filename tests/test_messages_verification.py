import sys
from pathlib import Path
import urllib.request
import json

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "ai-backend"))

from src.core.security import create_access_token

def test_messages_endpoint():
    token = create_access_token("eff46c06-37ca-4f61-a7d0-f926d14b0df2", "test@example.com")
    conv_id = "395de146-4fdd-40ea-a972-a294b422a8ad"

    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )

    with urllib.request.urlopen(req) as resp:
        status_code = resp.status
        data = json.loads(resp.read().decode("utf-8"))

    print(f"HTTP Status: {status_code}")
    print(f"Conversation ID: {data['conversation']['id']}")
    print(f"Total messages returned: {data['total']}")

    for i, m in enumerate(data.get("messages", [])):
        print(f"Message [{i+1}] ID: {m['id']} | Role: {m['role']} | Status: {m.get('status')} | Source: {m.get('source')} | Updated: {m.get('updated_at')}")

    assert status_code == 200, f"Expected 200, got {status_code}"
    assert data["total"] == 4, f"Expected 4 messages, got {data['total']}"
    for m in data["messages"]:
        assert m.get("status") == "COMPLETED", f"Expected COMPLETED, got {m.get('status')}"
        assert m.get("updated_at") is not None, "updated_at should not be None"

    print("\n>>> ALL QA VERIFICATION ASSERTIONS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_messages_endpoint()

