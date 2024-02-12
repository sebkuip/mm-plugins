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
        name = ctx.thread.recipient.display_name if ctx.thread.recipient is discord.Member else ctx.thread.recipient.name
        print(type(ctx.thread.recipient))
        await ctx.send(name)

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        await thread.channel.send(thread.recipient.id)
        name = thread.recipient.display_name if thread.recipient is discord.Member else thread.recipient.name
        await thread.channel.send(name)


async def setup(bot):
    await bot.add_cog(Userid_lister(bot))