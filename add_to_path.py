"""
Run this ONCE with the SAME Python you use for streamlit:
    python add_to_path.py
"""
import sys, os, site

project_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Python:      {sys.executable}")
print(f"Project dir: {project_dir}")

# Find the site-packages folder that belongs to THIS Python executable
sp_list = site.getsitepackages()
print(f"Site-packages locations:")
for sp in sp_list:
    print(f"  {sp}")

# Write to the first writable one
for sp in sp_list:
    if not os.path.isdir(sp):
        continue
    pth = os.path.join(sp, "lead_intelligence.pth")
    try:
        with open(pth, "w") as f:
            f.write(project_dir + "\n")
        print(f"\n✅ Registered at: {pth}")
        break
    except Exception as e:
        print(f"  Could not write to {pth}: {e}")
else:
    print("\n❌ Failed. Run as Administrator or try the PYTHONPATH method below.")
    print(f'\n   PowerShell: $env:PYTHONPATH = "{project_dir}"; streamlit run streamlit_app.py')
    sys.exit(1)

# Quick sanity check
sys.path.insert(0, project_dir)
try:
    import core.database
    print("✅ core.database import OK")
    print("\nNow run:  streamlit run streamlit_app.py")
except ImportError as e:
    print(f"❌ Still failing: {e}")