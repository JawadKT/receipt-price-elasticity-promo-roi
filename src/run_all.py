import runpy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# just fire the three stages in order
for step in ["run_price_change_detection", "run_elasticity", "run_promo_simulation"]:
    print(f"\n=== {step} ===")
    runpy.run_module(step, run_name="__main__")
