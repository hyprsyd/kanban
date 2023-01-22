from main import api
import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:api", debug=True)
