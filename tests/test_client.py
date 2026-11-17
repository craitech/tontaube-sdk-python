import asyncio
import base64
import json

import httpx
import pytest

import tontaube

VOICE_ID = "6f1c2b9e-0d3a-4c55-9a7e-1f2b3c4d5e6f"


def make_client(handler):
    client = tontaube.Client(api_key="ttb_test")
    client._http_client = httpx.Client(
        base_url=client.base_url, headers=client._headers, transport=httpx.MockTransport(handler)
    )
    return client


def make_async_client(handler):
    client = tontaube.AsyncClient(api_key="ttb_test")
    client._http_client = httpx.AsyncClient(
        base_url=client.base_url, headers=client._headers, transport=httpx.MockTransport(handler)
    )
    return client


def test_generate_binary_keeps_old_call_style():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        seen["headers"] = request.headers
        return httpx.Response(
            200,
            content=b"mp4",
            headers={"content-type": "audio/mp4; codecs=opus", "x-cost-usd": "0.000120", "x-balance-usd": "4.99"},
        )

    with make_client(handler) as client:
        response = client.generate_speech("Hello", VOICE_ID, "en", None, 0.8)

    assert seen["body"] == {"text": "Hello", "voice_id": VOICE_ID, "language": "en", "temperature": 0.8}
    assert seen["headers"]["x-api-key"] == "ttb_test"
    assert seen["headers"]["content-type"] == "application/json"
    assert response.content == b"mp4"
    assert response.cost_usd == 0.00012
    assert response.balance_usd == 4.99


def test_generate_json_with_context_and_timestamps():
    def handler(request):
        body = json.loads(request.content)
        assert body["return_context"] is True and body["include_timestamps"] is True
        assert body["controls"] == {"rate": 1}
        assert body["prefix"] == {"text": "Before.", "context": [{"ref": "ttc1.a", "start": 0, "end": 10}, {"silence": 3}]}
        return httpx.Response(
            200,
            json={
                "audio_b64": base64.b64encode(b"RIFF").decode(),
                "mime_type": "audio/wav",
                "sample_rate": 24000,
                "duration": 0.8,
                "seed": 7,
                "context": "ttc1.b",
                "n_frames": 10,
                "frame_hz": 12.5,
                "model_version": "TontaubeV1.1",
                "cost_usd": "0.000010",
                "balance_usd": "4.000000",
                "request_id": "abc",
                "timestamps": {
                    "text": "Hi.",
                    "words": [{"text": "Hi.", "start": 0.1, "end": None, "char_start": 0, "char_end": 3, "confidence": 0.9}],
                    "characters": [{"char": "H", "index": 0, "start": 0.1, "end": 0.2}],
                },
            },
            headers={"x-seed": "7", "x-request-id": "abc"},
        )

    with make_client(handler) as client:
        response = client.generate_speech(
            "Hi.",
            voice_id=VOICE_ID,
            controls={"rate": 1},
            prefix=tontaube.Prefix(text="Before.", context=[{"ref": "ttc1.a", "start": 0, "end": 10}, tontaube.Silence(silence=3)]),
            return_context=True,
            include_timestamps=True,
        )

    assert response.content == b"RIFF"
    assert response.mime_type == "audio/wav"
    assert response.audio_duration == 0.8
    assert response.seed == 7 and response.n_frames == 10
    assert response.timestamps.words[0].end is None
    assert response.context_slice(2) == tontaube.ContextSlice(ref="ttc1.b", start=2, end=10)


def test_voice_audio_is_sent_as_base64(tmp_path):
    path = tmp_path / "reference.wav"
    path.write_bytes(b"voice")

    def handler(request):
        body = json.loads(request.content)
        assert body["voice_audio_b64"] == base64.b64encode(b"voice").decode()
        assert "voice_id" not in body
        return httpx.Response(200, content=b"mp4")

    with make_client(handler) as client:
        assert client.generate_speech("Hi", voice_audio=path).content == b"mp4"


def test_request_validation():
    with pytest.raises(ValueError):
        tontaube.GenerateRequest(text="Hi")
    with pytest.raises(ValueError):
        tontaube.GenerateRequest(text="Hi", voice_id=VOICE_ID, speaker_id=VOICE_ID)
    with pytest.raises(ValueError):
        tontaube.GenerateRequest(text="x" * 2001, voice_id=VOICE_ID, seed=1)
    with pytest.raises(ValueError):
        tontaube.GenerateRequest(text="Hi", voice_id=VOICE_ID, audio_format="wav")
    with pytest.raises(ValueError):
        tontaube.GenerateRequest(text="Hi", voice_id=VOICE_ID, controls={"speed": 1})
    with pytest.raises(ValueError):
        tontaube.StreamRequest(text="x" * 6001, voice_id=VOICE_ID)
    with pytest.raises(ValueError):
        tontaube.StreamRequest(text="Hi", voice_id=VOICE_ID, return_context=True)
    with pytest.raises(ValueError):
        tontaube.StreamRequest(text="Hi", voice_id=VOICE_ID, include_timestamps=True)
    stream = tontaube.StreamRequest(
        text="Hi", voice_id=VOICE_ID, style="agentic", seed=3, prefix={"text": "Before.", "context": [{"silence": 2}]}
    )
    assert stream.model_dump(exclude_none=True)["style"] == "agentic"
    assert tontaube.GenerateRequest(text="x" * 2001, voice_id=VOICE_ID).text


def test_voices_crud(tmp_path):
    reference = tmp_path / "me.wav"
    reference.write_bytes(b"wav")
    custom = {
        "id": VOICE_ID, "name": "Me", "type": "custom", "languages": ["en"], "language": "en",
        "duration_seconds": 12.0, "created_at": "2026-11-17T10:00:00Z", "model_version": "TontaubeV1.1",
        "n_codebooks": 8, "codec": "dualcodec_12hz_v1",
    }
    library = {"id": "lib", "name": "Narrator", "type": "library", "languages": [], "gender": "female", "voice_style": "Narration"}

    def handler(request):
        if request.method == "POST":
            content_type = request.headers["content-type"]
            assert content_type.startswith("multipart/form-data")
            assert b'name="name"' in request.content and b"Me" in request.content
            assert b'filename="me.wav"' in request.content
            return httpx.Response(201, json=custom)
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path.endswith("/voices"):
            assert request.url.params.get("type") == "library"
            return httpx.Response(200, json=[library])
        return httpx.Response(200, json=custom)

    with make_client(handler) as client:
        created = client.create_voice("Me", reference, language="en")
        assert created.type == "custom" and created.n_codebooks == 8
        assert client.list_voices(type="library")[0].voice_style == "Narration"
        assert client.get_voice(VOICE_ID).name == "Me"
        assert client.delete_voice(VOICE_ID) is None


def test_api_error_carries_code():
    def handler(request):
        return httpx.Response(404, json={"detail": {"error": "voice_not_found", "message": "Voice not found"}})

    with make_client(handler) as client:
        with pytest.raises(tontaube.APIError) as error:
            client.get_voice(VOICE_ID)

    assert error.value.status_code == 404
    assert error.value.code == "voice_not_found"
    assert isinstance(error.value, httpx.HTTPStatusError)


def test_validation_error_message():
    def handler(request):
        return httpx.Response(422, json={"detail": [{"loc": ["body", "text"], "msg": "Field required"}]})

    with make_client(handler) as client:
        with pytest.raises(tontaube.APIError) as error:
            client.generate_speech("Hi", VOICE_ID)

    assert error.value.code == "invalid_request"
    assert "Field required" in error.value.message


def test_outdated_sdk():
    def handler(request):
        return httpx.Response(426, json={"message": "Too old."})

    with make_client(handler) as client:
        with pytest.raises(tontaube.OutdatedSDKError):
            client.list_voices()


def test_stream_yields_chunks_and_raises_errors():
    def handler(request):
        body = json.loads(request.content)
        if body["text"] == "fail":
            return httpx.Response(402, json={"detail": {"error": "insufficient_balance", "message": "No balance"}})
        return httpx.Response(200, content=b"abcdef", headers={"content-type": "audio/mpeg"})

    with make_client(handler) as client:
        assert b"".join(client.stream_speech("Hi", VOICE_ID)) == b"abcdef"
        assert b"".join(client.stream_speech("x" * 3000, VOICE_ID, style="conversational", seed=1)) == b"abcdef"
        with pytest.raises(ValueError):
            list(client.stream_speech("x" * 6001, VOICE_ID, style="conversational"))
        with pytest.raises(tontaube.APIError) as error:
            list(client.stream_speech("fail", VOICE_ID))
        assert error.value.code == "insufficient_balance"
        with pytest.raises(ValueError):
            list(client.stream_speech("x" * 6001, VOICE_ID))


def test_async_client():
    def handler(request):
        if request.url.path.endswith("/speech/stream"):
            return httpx.Response(200, content=b"mp3")
        if request.url.path.endswith("/voices"):
            return httpx.Response(200, json=[{"id": "lib", "name": "Narrator", "type": "library"}])
        return httpx.Response(200, content=b"mp4")

    async def run():
        async with make_async_client(handler) as client:
            voices = await client.list_voices()
            response = await client.generate_speech("Hi", voices[0].id)
            chunks = [chunk async for chunk in client.stream_speech("Hi", voices[0].id)]
            return response.content, b"".join(chunks)

    assert asyncio.run(run()) == (b"mp4", b"mp3")
