import asyncio
import shutil
import aiofiles

from models import TextToVoiceRequest, Audio
from aiohttp import ClientSession
from config import env


class Voice:
    def __init__(self, request: TextToVoiceRequest):
        self.request = request

    async def text_to_voice(self) -> Audio:
        async with ClientSession() as sess:
            async with sess.post(f"https://api.elevenlabs.io/v1/text-to-speech/{env.LEARN_VOICE_ID}/stream", json={
                "model_id": "eleven_multilingual_v2",
                "text": self.request.content,
                "voice_settings": {
                    "similarity_boost": 1,
                    "stability": 1,
                    "style": 1,
                    "use_speaker_boost": True
                }
            }, headers={"Content-Type": "application/json", "xi-api-key": env.ELEVENLABS_API_KEY}) as response:
                if response.status == 200:
                    chunk_size = 8192 # 8 KB
                    chunk: bytes
                    async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        async with aiofiles.open(temp_file.name, "wb") as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                            await file.close()
                        await temp_file.close()

                        shutil.move(temp_file.name, f"{temp_file.name}.mp3")
                        return Audio(
                            success=True,
                            absolute_path=f"{temp_file.name}.mp3"
                        )
                return Audio()


if __name__ == "__main__":
    voice = Voice(TextToVoiceRequest(content="Test"))
    loop = asyncio.get_event_loop()
    audio: Audio = loop.run_until_complete(voice.text_to_voice())
    print(f"Audio downloaded: {audio.success}; path: {audio.absolute_path};")
