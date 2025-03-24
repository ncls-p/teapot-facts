import os

import uvicorn

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Run the server
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
    )
