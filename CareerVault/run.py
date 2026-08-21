import uvicorn


if __name__ == "__main__":
    uvicorn.run("careervault.main:app", host="127.0.0.1", port=8766, reload=False)
