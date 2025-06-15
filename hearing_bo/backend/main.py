# backend/main.py

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from audio import list_audio_devices, generate_tone, play_audio
from bo_logic import BayesianCurveFitter

app = FastAPI()

bo_fitter = BayesianCurveFitter(freq_range=(40, 16000))

@app.get("/")
async def get_index():
    return FileResponse('../frontend/index.html')

@app.get("/api/devices")
async def get_audio_devices():
    return list_audio_devices()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    test_state = {
        "device_id": None,
        "root_freq": 1000.0,
        "root_volume": -25.0,
        "current_test_points": {} # e.g., {"low": 120, "mid": 750, "high": 6000}
    }

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "start_test":
                bo_fitter.reset()
                test_state["device_id"] = int(message["device_id"])
                test_state["root_freq"] = float(message["root_freq"])
                test_state["root_volume"] = float(message["root_volume"])

                # Add the root point automatically (as a single point)
                bo_fitter.add_points([test_state["root_freq"]], [test_state["root_volume"]])

                # Get the first set of points to test
                next_points = bo_fitter.get_next_points_stratified()
                test_state["current_test_points"] = next_points
                
                await websocket.send_text(json.dumps({"type": "test_started"}))
                await websocket.send_text(json.dumps({
                    "type": "new_points", 
                    "points": next_points
                }))

            elif msg_type == "play_tone":
                # Generic tone player
                freq = float(message["frequency"])
                vol = float(message["volume"])
                tone = generate_tone(freq, vol)
                play_audio(test_state["device_id"], tone)

            elif msg_type == "submit_volumes":
                # User submits the volumes for the 3 test frequencies
                submissions = message["submissions"] # e.g., [{"freq": 120, "vol": -30}, ...]
                
                freqs = [s["freq"] for s in submissions]
                volumes = [s["vol"] for s in submissions]
                
                # Update the model with the batch of new points
                bo_fitter.add_points(freqs, volumes)
                bo_fitter.fit_model()
                
                # Get the next set of points to test
                next_points = bo_fitter.get_next_points_stratified()
                test_state["current_test_points"] = next_points

                # Send updated curve data to the frontend
                curve_data = bo_fitter.get_full_curve()
                await websocket.send_text(json.dumps({
                    "type": "update_curve",
                    "data": curve_data
                }))
                
                # Send the next set of points to test
                await websocket.send_text(json.dumps({
                    "type": "new_points",
                    "points": next_points
                }))

    except WebSocketDisconnect:
        print("Client disconnected.")