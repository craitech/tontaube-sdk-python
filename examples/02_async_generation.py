import asyncio
import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")

async def main():
    async with tontaube.AsyncClient(api_key=API_KEY) as client:
        speakers = await client.list_speakers()
        for speaker in speakers:
            print(f"{speaker.name} ({speaker.voice_style}), id: {speaker.id}")

        response = await client.generate_speech(
            text="I am here to help you with your project. Tell me what we are building today, and I will get right to work.",
            speaker_id=speakers[0].id,
            language="en",
            format="wav",
            temperature=0.8,
        )

        with open("speech.wav", "wb") as f:
            f.write(response.content)

        print(f"Duration: {response.audio_duration}s, Cost: ${response.cost_usd}")
        print(f"Result saved to speech.wav")

asyncio.run(main())
