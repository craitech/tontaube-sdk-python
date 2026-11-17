import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")
REFERENCE = "reference.wav"

with tontaube.Client(api_key=API_KEY) as client:
    voice = client.create_voice(name="My voice", audio=REFERENCE, language="en")
    print(f"Created {voice.name} ({voice.duration_seconds}s of reference audio), id: {voice.id}")

    response = client.generate_speech(
        text="This is my own voice, cloned from a short recording.",
        voice_id=voice.id,
    )

    with open("my_voice.m4a", "wb") as f:
        f.write(response.content)

    client.delete_voice(voice.id)

print("Result saved to my_voice.m4a")
