import discord
from discord.ext import commands


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="join")
    async def join(self, ctx: commands.Context) -> None:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("음성 채널에 먼저 입장해주세요.")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"{channel.name}에 입장했습니다.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("음성 채널에서 나갔습니다.")
        else:
            await ctx.send("봇이 음성 채널에 없습니다.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceCog(bot))
