from app import create_app

app = create_app()


@app.get("/health")
def health_check():
    return {
        "success": True,
        "message": "Healthcare AI Backend is running"
    }, 200


if __name__ == "__main__":
    app.run(debug=True)