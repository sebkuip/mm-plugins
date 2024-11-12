from discord.ext import commands

class MNFHDMLimiter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif message.channel.id not in (721750845749723236, 1065831118970040340):
            return
        elif message.author.guild_permissions.manage_messages:
            return
        elif len(message.content) > 100:
            await message.reply("This channel is only for asking people to DM with you. Intro's or other long messages are not allowed.", delete_after=10)
            await message.delete()

async def setup(bot):
    await bot.add_cog(MNFHDMLimiter(bot))