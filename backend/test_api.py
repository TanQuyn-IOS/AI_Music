"""Kiểm tra API hiện tại của ACE-Step Space."""
import os, sys, json, time

def main():
    from gradio_client import Client
    HF_TOKEN = os.getenv("HF_TOKEN", "")
    print("Connecting...")
    try:
        c = Client("ACE-Step/ACE-Step", token=HF_TOKEN or None, verbose=False)
        print("Connected!")
        info = c.view_api(return_format="dict")
        call_ep = info.get("named_endpoints", {}).get("/__call__", {})
        params = call_ep.get("parameters", [])
        print(f"\n=== /__call__ has {len(params)} params ===")
        for p in params:
            label = p.get("label", "?")
            ptype = p.get("python_type", {}).get("type", "?")
            default = p.get("default", "REQUIRED")
            print(f"  {label}: {ptype} = {repr(default)}")
    except Exception as e:
        print(f"ACE-Step test skipped or offline: {e}")

if __name__ == '__main__':
    main()
