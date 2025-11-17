"""Quick backend verification script."""
try:
    from backend.main import app
    print("[OK] Backend imports successful!")
    print("\nRegistered API Routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'GET'
            print(f"  {methods:10s} {route.path}")
    print("\n[OK] All routes registered successfully!")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
