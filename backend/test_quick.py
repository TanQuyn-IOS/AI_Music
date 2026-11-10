"""Test nhanh MusicGen local."""
import os, sys, time

def main():
    import os, sys, time
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    sys.path.insert(0, '.')
    import django; django.setup()
    
    from apps.ai_engine.music_generator import generate_music
    
    print("Testing MusicGen local (15s)...")
    t0 = time.time()
    try:
        wav, sr = generate_music(
            prompt="vpop, Vietnamese pop, piano, romantic",
            duration=15,
            use_cache=False,
        )
        print(f"SUCCESS! {len(wav):,} bytes, {time.time()-t0:.1f}s, SR={sr}Hz")
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
