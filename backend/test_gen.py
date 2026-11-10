"""Test ACE-Step predict wrapper."""
import os, sys, time

def main():
    """Copy EXACT working code from test_replicate into wrapper pattern."""
    import os, sys, time
    os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', '')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    sys.path.insert(0, '.')
    import django; django.setup()
    
    # Reset singleton
    import apps.ai_engine.acestep_generator as ag
    ag._client = None
    
    # Patch get_client để thấy log
    from gradio_client import Client as _GClient
    
    def patched_client():
        c = _GClient("ACE-Step/ACE-Step", token=os.getenv('HF_TOKEN', ''), verbose=False)
        ag._client = c
        return c
    
    ag.get_client = patched_client
    
    # Gọi trực tiếp giống test_gen.py hoạt động
    print("Testing direct call (same as working test)...")
    try:
        c = patched_client()
        t0 = time.time()
        result = c.predict(
            30.0,
            "vpop, piano, romantic",
            "",
            30.0,
            15.0,
            "euler",
            "apg",
            10.0,
            "1132623236",
            0.5,
            0.0,
            3.0,
            True,
            False,
            True,
            "",
            0.0,
            0.0,
            False,
            0.5,
            None,
            "none",
            api_name="/__call__"
        )
        print(f"Result in {time.time()-t0:.1f}s:", result)
    except Exception as e:
        print(f"Direct call skipped or error: {e}")

if __name__ == '__main__':
    main()
