import boto3

from .settings import PollySettings


class PollyClient:
    def __init__(self, settings: PollySettings | None = None):
        self.settings = settings or PollySettings()
        self._client = boto3.client(
            "polly",
            aws_access_key_id=self.settings.access_key_id,
            aws_secret_access_key=self.settings.secret_access_key,
            region_name=self.settings.region_name,
        )

    def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        response = self._client.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id or self.settings.voice_id,
        )
        return response["AudioStream"].read()
