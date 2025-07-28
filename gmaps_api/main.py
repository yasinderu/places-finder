# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import schemas
import googlemaps

app = FastAPI(
    title="Places Finder API",
    description="API to find places (eat, recreation, go) and generate map links.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
GOOGLE_CLOUD_API_KEY=os.getenv("GOOGLE_CLOUD_API_KEY")
QEURIES_PER_SECOND=os.getenv("QEURIES_PER_SECOND", 60)
QEURIES_PER_MINUTE=os.getenv("QEURIES_PER_MINUTE", 6000)

def get_actual_response(delimiter:str, text:str):
    index = text.find(delimiter)
    return text[index + len(delimiter):].strip()

@app.post("/generate")
async def generate_text(request_body: schemas.PromptRequest):
    try:
        ollama_url = f"{OLLAMA_HOST}/api/generate"

        payload = schemas.PlacePayload(
            query=request_body.prompt
        )

        places_response = await find_places(payload=payload)

        places = places_response
        formatted_response = ""

        if places:
            formatted_response = "Use this data to answer:\n\n"
            for place in places:
                formatted_response += f"**{place['name']}**\n"
                formatted_response += f"Address: {place['address']}\n"
                formatted_response += f"[Get Directions on Google Maps]({place['google_maps_url']})\n"

        payload = {
            "model": "qwen3:4b",
            "prompt": f"${formatted_response}Question: {request_body.prompt}",
            "stream": False
        }
        print(f"Sending request to Ollama: {ollama_url} with payload: {payload}")
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()

        answer = response.json()

        response = get_actual_response(delimiter="</think>", text=answer.get("response", ""))

        return schemas.ResponseLLM(
            model=answer.get("model", ""),
            response=response
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/")
async def root():
    return {"message": "FastAPI LLM App is running! Use /generate to interact with the model."}

async def find_places(payload: schemas.PlacePayload):
    """Helper to Finds places based on the query and returns map information."""
    try:

        gmaps = googlemaps.Client(key=GOOGLE_CLOUD_API_KEY, queries_per_second=int(QEURIES_PER_SECOND), queries_per_minute=QEURIES_PER_MINUTE)

        query_lower = payload.query.lower()

        places_result = gmaps.places(query=query_lower, fields=["name", "formatted_address", "geometry", "url"])

        places = places_result["results"]

        if not places:
            return None
        
        found_places = []

        for place in places:
            found_places.append({
                    "name": place.get('name'),
                    "address": place.get('formatted_address'),
                    "latitude":place['geometry']['location']['lat'],
                    "longitude":place['geometry']['location']['lng'],
                    "google_maps_url":place.get('url'),
                }
            )

        return found_places
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    