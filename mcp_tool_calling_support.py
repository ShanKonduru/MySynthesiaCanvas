#!/usr/bin/env python3
"""
Checks whether local Ollama models accept tool-calling (i.e. accept a `tools` payload).
Usage:
  - Install requests: pip install requests
  - Optionally set OLLAMA_BASE env var (default http://localhost:11434)
  - Run: python check_tool_support.py
"""

import os
import requests
import json
import textwrap

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434").rstrip("/")
CHAT_URL = OLLAMA_BASE + "/api/chat"
MODELS_TO_TEST = [
    "llama3.1:latest",
    "llama2:latest",
    "nomic-embed-text:latest",
    "mxbai-embed-large:latest",
    "deepseek-coder:latest",
    "qwen2.5:latest",
    "llama3:latest",
    "mistral:latest",
    "gemma3:latest",
]

# If your Ollama supports listing models, try to replace MODELS_TO_TEST automatically:
try:
    resp = requests.get(OLLAMA_BASE + "/api/models", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        # `data` shape can vary; try to extract model names if available
        names = []
        if isinstance(data, list):
            for item in data:
                # Common shapes: item could be {"name":"..."} or a string
                if isinstance(item, dict) and "name" in item:
                    names.append(item["name"])
                elif isinstance(item, str):
                    names.append(item)
        if names:
            MODELS_TO_TEST = names
except Exception:
    # ignore and fall back to static list
    pass


def test_model_tools(model_name: str):
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a tiny test assistant."},
            {"role": "user", "content": "Test: can you accept tools? (this is a machine test)"}
        ],
        "tools": [
            {
                "type": "openapi",
                "spec": textwrap.dedent(
                    """
                    openapi: 3.0.0
                    info:
                      title: tiny
                      version: 1.0.0
                    paths: {}
                    """
                )
            }
        ],
        "stream": False,
    }
    try:
        r = requests.post(CHAT_URL, json=payload, timeout=20)
    except Exception as e:
        return {"model": model_name, "status": "error", "reason": f"request exception: {e}"}

    # Interpret response
    if r.status_code == 200:
        # server accepted the tools payload — treat as "supports tools (accepted payload)"
        # (Note: model may still not *invoke* tools in dialogues, but this confirms Ollama accepted the tools argument)
        try:
            content = r.json()
        except Exception:
            content = r.text[:1000]
        return {"model": model_name, "status": "ok", "http_status": 200, "sample_response": content}
    else:
        # non-200: often 400 with message "does not support tools" or similar
        text = r.text or "<no body>"
        return {"model": model_name, "status": "rejected", "http_status": r.status_code, "body": text[:1000]}


def main():
    print("OLLAMA base:", OLLAMA_BASE)
    print("Testing models:", MODELS_TO_TEST)
    print()
    results = []
    for m in MODELS_TO_TEST:
        print(f" -> Testing {m} ...", end="", flush=True)
        res = test_model_tools(m)
        results.append(res)
        if res["status"] == "ok":
            print(" ACCEPTED")
        elif res["status"] == "rejected":
            print(f" REJECTED (status {res.get('http_status')})")
        else:
            print(" ERROR")
    print("\nSummary:\n")
    for r in results:
        print(f"- {r['model']}: {r['status']}", end="")
        if "http_status" in r:
            print(f" (http {r['http_status']})", end="")
        if r['status'] != 'ok':
            print(f" -> {r.get('reason') or r.get('body')[:200]}")
        else:
            print()
    print("\nNotes:")
    print(" - If you see a response body containing 'does not support tools' or HTTP 400, the model build does not support Ollama tools.")
    print(" - Embedding models (nomic-embed-text, mxbai-embed-large) generally do not support tools — they are for embeddings.")
    print("\nIf you want, paste the script output here and I’ll help interpret it.")

if __name__ == "__main__":
    main()
