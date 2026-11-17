import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")
REFERENCE = "reference.wav"

with tontaube.Client(api_key=API_KEY) as client:
    response = client.generate_speech(
        text="Nothing is stored: the voice comes straight from the recording sent with this request.",
        voice_audio=REFERENCE,
        language="en",
    )

with open("instant_clone.m4a", "wb") as f:
    f.write(response.content)

print("Result saved to instant_clone.m4a")
