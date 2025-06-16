# backend/main.py

import numpy as np
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from audio import list_audio_devices, generate_tone, play_audio
from bo_logic import BayesianCurveFitter

app = FastAPI()

# A singleton instance of our Bayesian optimizer
bo_fitter = BayesianCurveFitter(freq_range=(40, 16000))

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
        "device_id": None,
        "root_freq": 1000.0,
        "root_volume": -25.0,
        "current_test_freq": None,
        "seed_points": [],
        "seed_index": 0,
        "is_seeding": False,
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
                num_seed_points = int(message.get("num_seed_points", 5)) # Default to 5

                # Add the root point automatically
                bo_fitter.add_point(test_state["root_freq"], test_state["root_volume"])

                # --- NEW: Initial Seeding Logic with configurable count ---
                test_state["is_seeding"] = True
                
                # Generate N quasi-random points, avoiding the root frequency
                log_min, log_max = bo_fitter.log_freq_range
                
                # Use a set for efficient checking of proximity
                seed_log_freqs = {np.log10(test_state["root_freq"])}
                
                # Generate N random seed points + the root
                while len(seed_log_freqs) < num_seed_points + 1:
                    rand_log_freq = random.uniform(log_min, log_max)
                    # Ensure new random points are not too close to existing ones
                    if all(abs(rand_log_freq - s) > 0.1 for s in seed_log_freqs):
                         seed_log_freqs.add(rand_log_freq)
                
                # Remove the root frequency itself from the list of points to be tested
                seed_log_freqs.remove(np.log10(test_state["root_freq"]))
                
                test_state["seed_points"] = sorted([10**f for f in seed_log_freqs])
                test_state["seed_index"] = 0
                
                # Send the first seed point to test
                next_freq = test_state["seed_points"][0]
                test_state["current_test_freq"] = next_freq
                
                await websocket.send_text(json.dumps({
                    "type": "test_started",
                    "seeding_total": len(test_state["seed_points"])
                }))
                await websocket.send_text(json.dumps({
                    "type": "new_point", 
                    "frequency": next_freq,
                    "seeding_current": 1
                }))

            elif msg_type == "play_root":
                tone = generate_tone(test_state["root_freq"], test_state["root_volume"])
                play_audio(test_state["device_id"], tone)

            elif msg_type == "play_test":
                freq = test_state["current_test_freq"]
                vol = float(message["volume"])
                tone = generate_tone(freq, vol)
                play_audio(test_state["device_id"], tone)

            elif msg_type == "submit_volume":
                freq = test_state["current_test_freq"]
                vol = float(message["volume"])
                bo_fitter.add_point(freq, vol)

                next_freq = None
                seeding_payload = {"seeding_current": 0}

                if test_state["is_seeding"]:
                    test_state["seed_index"] += 1
                    if test_state["seed_index"] < len(test_state["seed_points"]):
                        # --- More seed points to test ---
                        next_freq = test_state["seed_points"][test_state["seed_index"]]
                        seeding_payload["seeding_current"] = test_state["seed_index"] + 1
                    else:
                        # --- Seeding finished ---
                        test_state["is_seeding"] = False
                        bo_fitter.fit_model()
                        next_freq = bo_fitter.get_next_point()
                else:
                    # --- Normal BO loop ---
                    bo_fitter.fit_model()
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
                    "frequency": next_freq,
                    **seeding_payload
                }))

    except WebSocketDisconnect:
        print("Client disconnected.")