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

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        rate: int = 100,
        pitch: int = 0
    ) -> bytes:
        """Synthesize speech with rate and pitch control.

        Args:
            text: Text to synthesize
            voice_id: Voice ID to use (optional)
            rate: Speech rate percentage (20-200, default: 100)
            pitch: Speech pitch offset (-50 to +50, default: 0)

        Returns:
            Audio data as bytes
        """
        # Convert int to percentage strings for AWS Polly SSML
        rate_str = f"{rate}%"
        pitch_str = f"{pitch:+d}%" if pitch != 0 else "0%"

        # Create SSML with prosody tags for rate and pitch
        ssml_text = f'<speak><prosody rate="{rate_str}" pitch="{pitch_str}">{text}</prosody></speak>'

        response = self._client.synthesize_speech(
            Text=ssml_text,
            TextType="ssml",  # Use SSML instead of plain text
            OutputFormat="mp3",
            VoiceId=voice_id or self.settings.voice_id,
        )
        return response["AudioStream"].read()
