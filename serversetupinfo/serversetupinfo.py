import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class ServerSetupInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_permissions(self, user: discord.Member):
        if await self.bot.is_owner(user) or user == self.bot.user.id:
            return PermissionLevel.OWNER
        permissions = PermissionLevel.ADMINISTRATOR if user.guild_permissions.administrator else PermissionLevel.REGULAR
        checkables = user.roles.extend([user])

        for level in PermissionLevel:
            for value in checkables:
                if level > permissions and value in self.bot.config["command_permissions"][level]:
                    permissions = level
        return permissions

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command(name="ssu", help="Displays the server startup information")
    @commands.cooldown(1, 3600, type=commands.BucketType.guild)
    async def ssu(self, ctx: commands.Context):
        info_embed=discord.Embed(title="London Server Startup", description=f"  Come and visit the City of London! There is a server startup ongoing!\n\n  https://www.roblox.com/games/17428786424/City-of-London\n\n  **SSU hosted by {ctx.author.mention}>**", color=0x013a93, url="https://www.roblox.com/games/17428786424/City-of-London")
        info_embed.set_author(name="United Kingdom")
        info_embed.set_footer(text="Updated at")
        info_embed.timestamp = ctx.message.created_at
        info_embed.set_image("https://images-ext-1.discordapp.net/external/8eftouOgKVHU3gYu0C7hH1v65Vm7mXy6dRMhwcv5Zfc/https/i.ibb.co/wdcTLdc/Webp-34.png")

        log_embed=discord.Embed(title="ssu command ran", description=f"  **{ctx.author.mention}** ran the ssu command", color=0x013a93)
        log_embed.add_field(name="Permissions", value=await self.get_permissions(ctx.author), inline=False)
        log_embed.set_footer(text="Ran at")
        log_embed.timestamp = ctx.message.created_at

        info_channel = self.bot.get_channel(1068935113183858788)
        log_channel = self.bot.get_channel(1066377714438787134)

        await info_channel.send(embed=info_embed)
        await log_channel.send(embed=log_embed)

    @ssu.error
    async def ssu_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=discord.Embed(title="Error", description="You do not have the required permissions to run this command.", color=0xff0000))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=discord.Embed(title="Error", description=f"This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.", color=0xff0000))
        else:
            raise error

async def setup(bot):
    await bot.add_cog(ServerSetupInfo(bot))