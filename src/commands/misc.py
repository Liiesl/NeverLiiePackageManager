# src/commands/misc.py
from .. import registry

def list_registry(args):
    items = registry.list_libraries()
    if not items:
        print("Registry empty.")
        return
        
    print(f"Registry Libraries:")
    for name, latest, lang, frame in items:
        meta = []
        if lang: meta.append(lang)
        if frame and frame != "none": meta.append(frame)
        
        meta_str = f" [{'/'.join(meta)}]" if meta else ""
        
        print(f"📦 {name} (Latest: {latest}){meta_str}")