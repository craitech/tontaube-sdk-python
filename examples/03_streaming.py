import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")

with tontaube.Client(api_key=API_KEY) as client:
    voice = client.list_voices(type="library")[0]

    with open("stream.mp3", "wb") as f:
        for chunk in client.stream_speech(
            text="Streaming starts delivering audio while the rest of the speech is still being generated.",
            voice_id=voice.id,
        ):
            f.write(chunk)

print("Result saved to stream.mp3")
