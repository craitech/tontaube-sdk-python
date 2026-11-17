import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")

with tontaube.Client(api_key=API_KEY) as client:
    voice = next(v for v in client.list_voices(type="library") if "en" in v.languages)

    response = client.generate_speech(
        text="Every word comes with the moment it is spoken.",
        voice_id=voice.id,
        include_timestamps=True,
    )

for word in response.timestamps.words:
    print(f"{word.start}s - {word.end}s  {word.text}")

with open("timestamps.m4a", "wb") as f:
    f.write(response.content)

print("Result saved to timestamps.m4a")
