from core import checks
from core.models import PermissionLevel

import discord
from discord.ext import commands

class VcMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.access_role = None
        self.block_role = None

        print(self.access_role)
        print(self.block_role)

    async def cog_load(self):
        await self.get_roles()

    async def get_roles(self):
        guild = self.bot.get_guild(685715989891121152)
        await guild.fetch_roles()
        self.access_role = guild.get_role(1170162673057550366)
        self.block_role = guild.get_role(1171343228411318314)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @commands.group(invoke_without_command=True)
    async def voicemod(self, ctx):
        """Voicemod help"""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @voicemod.command(name="give", aliases=["allow"])
    async def give(self, ctx, member: discord.Member):
        if self.access_role is None:
            await self.get_roles()
        await member.remove_roles(*self.block_role)
        await member.add_roles(*self.access_role)
        await ctx.send("Gave permissions to {member}")

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @voicemod.command(name="block", aliases=["disallow"])
    async def block(self, ctx, member: discord.Member):
        if self.access_role is None:
            await self.get_roles()
        await member.remove_roles(*self.access_role)
        await member.add_roles(*self.block_role)
        await ctx.send("Blocked permissions from {member}")

async def setup(bot):
    await bot.add_cog(VcMod(bot))