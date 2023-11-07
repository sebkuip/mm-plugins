from core import checks
from core.models import PermissionLevel

import discord
from discord.ext import commands

class VcMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.access_role = None
        self.block_role = None

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
    @voicemod.command(name="give", aliases=["allow"], help="Allow green voice chat access to a user.")
    async def give(self, ctx, member: discord.Member):
        if self.access_role is None:
            await self.get_roles()
        await member.remove_roles(*[self.block_role,])
        await member.add_roles(*[self.access_role,])
        await ctx.reply(f"Done! {member} has been given the <@&1170162673057550366> role, and (if present) the <@&1171343228411318314> role has been removed.")

    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @voicemod.command(name="block", aliases=["disallow"], help="Blocks green voice chat access from a user. Please make sure to run tatsu's commands as instructed.")
    async def block(self, ctx, member: discord.Member):
        if self.access_role is None:
            await self.get_roles()
        await member.remove_roles(*[self.access_role,])
        await member.add_roles(*[self.block_role,])
        await ctx.reply(f"Done! Blocked access for {member}\n"
        "**WARNING:** For this command to work, you must **FIRST** run `t@score [userid]` to remove all of the user's points from the tatsu bot. (Use the “Penalize user score” option.) Otherwise tatsu will give them access again! "
        "**AFTER** that is done, run this command again to give them the <@&1171343228411318314> role (This role prevents tatsu from giving access again!).\n"
        "This command also removes the <@&1170162673057550366> role if present."
        )

async def setup(bot):
    await bot.add_cog(VcMod(bot))