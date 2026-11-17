import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")

with tontaube.Client(api_key=API_KEY) as client:
    voice = client.list_voices(type="library")[0]

    response = client.generate_speech(
        text="Slow down, take a breath, and let the words land.",
        voice_id=voice.id,
        style="conversational",
        controls=tontaube.Controls(rate=1, pause=3, pitch_range=4),
        seed=42,
    )

with open("styled.m4a", "wb") as f:
    f.write(response.content)

print(f"Seed: {response.seed}")
print("Result saved to styled.m4a")
