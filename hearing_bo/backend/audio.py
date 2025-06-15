# backend/audio.py

import sounddevice as sd
import numpy as np

SAMPLE_RATE = 48000  # Hz

def list_audio_devices():
    """Lists available audio output devices."""
    devices = sd.query_devices()
    output_devices = []
    for i, device in enumerate(devices):
        # The condition checks for available output channels and a valid API
        if device['max_output_channels'] > 0:
            output_devices.append({'id': i, 'name': device['name']})
    return output_devices

def dbfs_to_amplitude(dbfs):
    """Converts dBFS value to a linear amplitude between 0 and 1."""
    return 10**(dbfs / 20.0)

def generate_tone(frequency: float, volume_dbfs: float, duration_s: float = 0.5):
    """Generates a sine wave tone as a NumPy array."""
    amplitude = dbfs_to_amplitude(volume_dbfs)
    t = np.linspace(0, duration_s, int(SAMPLE_RATE * duration_s), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    # Fade in/out to avoid clicks
    fade_len = int(SAMPLE_RATE * 0.01) # 10ms fade
    fade_in = np.linspace(0., 1., fade_len)
    fade_out = np.linspace(1., 0., fade_len)
    tone[:fade_len] *= fade_in
    tone[-fade_len:] *= fade_out
    return (amplitude * tone).astype(np.float32)

def play_audio(device_id: int, audio_data: np.ndarray):
    """Plays a NumPy audio array on a specific audio device."""
    try:
        sd.play(audio_data, samplerate=SAMPLE_RATE, device=device_id, blocking=False)
    except Exception as e:
        print(f"Error playing audio on device {device_id}: {e}")
        # Optionally, you could send an error back to the frontend