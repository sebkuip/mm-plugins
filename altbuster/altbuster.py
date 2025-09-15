import discord
from discord.ext import commands, tasks
import re

from core import checks
from core.models import PermissionLevel

class AltBuster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.default_config = {
            "enabled": False,
            "usernames": [],
            "messages": [],
            "pending_users": []
        }
        self.process_pending_users.start()

    async def cog_load(self):
        self.config = await self.db.find_one({"_id": "altbuster"})
        if not self.config:
            self.config = self.default_config
            await self.update_config()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "altbuster"},
            {"$set": self.config},
            upsert=True,
        )

    @commands.group(name="altbuster", invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster(self, ctx):
        """Manage the alt buster settings."""
        await ctx.send_help(ctx.command)

    @altbuster.command(name="toggle", help="Enable or disable the alt buster")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_toggle(self, ctx):
        self.config["enabled"] = not self.config["enabled"]
        await self.update_config()
        status = "enabled" if self.config["enabled"] else "disabled"
        await ctx.send(f"Alt Buster has been {status}.")

    @altbuster.command(name="addusername", help="Add a username to the alt list")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_addusername(self, ctx, *, username: str):
        if username in self.config["usernames"]:
            await ctx.send("This username is already in the alt list.")
            return
        self.config["usernames"].append(username)
        await self.update_config()
        await ctx.send(f"Added '{username}' to the alt list.")

    @altbuster.command(name="removeusername", help="Remove a username from the alt list")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_removeusername(self, ctx, *, username: str):
        if username not in self.config["usernames"]:
            await ctx.send("This username is not in the alt list.")
            return
        self.config["usernames"].remove(username)
        await self.update_config()
        await ctx.send(f"Removed '{username}' from the alt list.")

    @altbuster.command(name="setmessage", help="Set the message for the alt buster")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_setmessage(self, ctx, *, message: str):
        self.config["messages"].append(message)
        await self.update_config()
        await ctx.send("Added a new message for the alt buster.")

    @altbuster.command(name="removemessage", help="Remove a message from the alt buster")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_removemessage(self, ctx, *, message: str):
        if message not in self.config["messages"]:
            await ctx.send("This message is not in the alt buster list.")
            return
        self.config["messages"].remove(message)
        await self.update_config()
        await ctx.send("Removed the message from the alt buster list.")

    @altbuster.command(name="listusernames", help="List all usernames in the alt list")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_listusernames(self, ctx):
        if not self.config["usernames"]:
            await ctx.send("The alt list is empty.")
            return
        await ctx.send("Alt list usernames:\n" + "\n".join(self.config["usernames"]))

    @altbuster.command(name="listmessages", help="List all messages in the alt buster")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_listmessages(self, ctx):
        if not self.config["messages"]:
            await ctx.send("The alt buster messages list is empty.")
            return
        await ctx.send("Alt buster messages:\n" + "\n".join(self.config["messages"]))

    @altbuster.command(name="listpending", help="List all pending users to be banned")
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def altbuster_listpending(self, ctx):
        if not self.config["pending_users"]:
            await ctx.send("There are no pending users to be banned.")
            return
        await ctx.send("Pending users to be banned:\n" + "\n".join(map(str, self.config["pending_users"])))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.config["enabled"] or member.bot:
            return

        if member.id in self.config["pending_users"]:
            return

        for username in self.config["usernames"]:
            if re.search(username, member.name, re.IGNORECASE):
                self.config["pending_users"].append(member.id)
                await self.update_config()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.config["enabled"]:
            return

        if message.author.id in self.config["pending_users"]:
            return

        for msg in self.config["messages"]:
            if re.search(msg, message.content, re.IGNORECASE):
                self.config["pending_users"].append(message.author.id)
                await self.update_config()
                return

    @tasks.loop(hours=24)
    async def process_pending_users(self):
        guild: discord.Guild = self.bot.guilds[0]  # Assuming the bot is only in one guild
        for user_id in self.config["pending_users"]:
            try:
                await guild.ban(discord.Object(id=user_id), reason="Alt Buster action")
            except Exception as e:
                print(f"Failed to ban user {user_id}: {e}")
        self.config["pending_users"].clear()
        await self.update_config()

async def setup(bot):
    await bot.add_cog(AltBuster(bot))