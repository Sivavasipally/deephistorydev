"""Start the FastAPI backend server."""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  Git History Analysis API - Backend Server")
    print("=" * 60)
    print()
    print("Starting FastAPI server...")
    print("  - URL: http://localhost:8000")
    print("  - API Docs: http://localhost:8000/api/docs")
    print("  - ReDoc: http://localhost:8000/api/redoc")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
