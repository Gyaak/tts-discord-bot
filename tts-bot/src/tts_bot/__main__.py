import discord
from .bot import TTSBot


def main() -> None:
    # Load opus library for voice support
    if not discord.opus.is_loaded():
        # Try to load opus from homebrew path
        try:
            discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')
        except Exception:
            try:
                # Fallback to system path
                discord.opus.load_opus('libopus.0.dylib')
            except Exception:
                print("Warning: Could not load opus library. Voice support may not work.")

    bot = TTSBot()
    bot.run_bot()


if __name__ == "__main__":
    main()
