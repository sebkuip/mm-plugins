from core import checks
from core.models import PermissionLevel

import discord
from discord.ext import commands

class VcMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        guild = self.bot.get_guild(685715989891121152)
        self.access_role = guild.get_role(1171348301501706390)
        self.block_role = guild.get_role(1171348301501706390)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @commands.group(invoke_without_command=True)
    async def voicemod(self, ctx):
        """Voicemod help"""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @voicemod.command(name="give", aliases=["allow"])
    async def give(self, ctx, member: discord.Member):
        await member.remove_roles(*self.block_role)
        await member.add_roles(*self.access_role)
        await ctx.send("Gave permissions to {member}")

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @voicemod.command(name="give", aliases=["disallow"])
    async def block(self, ctx, member: discord.Member):
        await member.remove_roles(*self.access_role)
        await member.add_roles(*self.block_role)
        await ctx.send("Blocked permissions from {member}")

async def setup(bot):
    await bot.add_cog(VcMod(bot))