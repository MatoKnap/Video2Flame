# backend/main.py

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audio import list_audio_devices, generate_tone, play_audio
from bo_logic import BayesianCurveFitter

app = FastAPI()

# A singleton instance of our Bayesian optimizer
bo_fitter = BayesianCurveFitter()

@app.get("/")
async def get_index():
    """Serves the main frontend file."""
    return FileResponse('../frontend/index.html')

@app.get("/api/devices")
async def get_audio_devices():
    """Endpoint to get a list of available audio output devices."""
    return list_audio_devices()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Store test state within the websocket connection scope
    test_state = {
        "ref_device_id": None,
        "test_device_id": None,
        "ref_volume": -20.0,
        "current_test_freq": None
    }

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "start_test":
                bo_fitter.reset()
                test_state["ref_device_id"] = int(message["ref_device_id"])
                test_state["test_device_id"] = int(message["test_device_id"])
                test_state["ref_volume"] = float(message["ref_volume"])

                # Add the reference point (1kHz) automatically
                bo_fitter.add_point(1000.0, test_state["ref_volume"])

                # Get the first point to test from the BO logic
                next_freq = bo_fitter.get_next_point()
                test_state["current_test_freq"] = next_freq
                
                await websocket.send_text(json.dumps({"type": "test_started"}))
                await websocket.send_text(json.dumps({
                    "type": "new_point", 
                    "frequency": next_freq
                }))

            elif msg_type == "play_reference":
                tone = generate_tone(1000.0, test_state["ref_volume"])
                play_audio(test_state["ref_device_id"], tone)

            elif msg_type == "play_test":
                freq = test_state["current_test_freq"]
                vol = float(message["volume"])
                tone = generate_tone(freq, vol)
                play_audio(test_state["test_device_id"], tone)

            elif msg_type == "submit_volume":
                freq = test_state["current_test_freq"]
                vol = float(message["volume"])
                
                # Update the model
                bo_fitter.add_point(freq, vol)
                bo_fitter.fit_model()
                
                # Get the next point to test
                next_freq = bo_fitter.get_next_point()
                test_state["current_test_freq"] = next_freq

                # Send updated curve data to the frontend
                curve_data = bo_fitter.get_full_curve()
                await websocket.send_text(json.dumps({
                    "type": "update_curve",
                    "data": curve_data
                }))
                
                # Send the next point to test
                await websocket.send_text(json.dumps({
                    "type": "new_point",
                    "frequency": next_freq
                }))

    except WebSocketDisconnect:
        print("Client disconnected.")