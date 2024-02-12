import discord
from discord.ext import commands

from core.checks import thread_only

class Userid_lister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @thread_only()
    async def userid(self, ctx):
        await ctx.send(ctx.thread.recipient.id)

    @commands.command()
    @thread_only()
    async def username(self, ctx):

        await ctx.send(ctx.thread.recipient.display_name)

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        await thread.channel.send(thread.recipient.id)
        await thread.channel.send(thread.recipient.display_name)


async def setup(bot):
    await bot.add_cog(Userid_lister(bot))