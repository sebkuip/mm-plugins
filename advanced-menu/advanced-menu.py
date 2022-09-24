from copy import copy
import traceback
import discord
from discord.ext import commands
from discord.ext.commands.view import StringView

from core import checks
from core.models import DummyMessage, PermissionLevel
from core.utils import normalize_alias

async def invoke_commands(alias, bot, thread, message):
    ctxs = []
    if alias is not None:
        ctxs = []
        aliases = normalize_alias(alias)
        for alias in aliases:
            view = StringView(bot.prefix + alias)
            ctx_ = commands.Context(prefix=bot.prefix, view=view, bot=bot, message=message)
            ctx_.thread = thread
            discord.utils.find(view.skip_string, await bot.get_prefix())
            ctx_.invoked_with = view.get_word().lower()
            ctx_.command = bot.all_commands.get(ctx_.invoked_with)
            ctxs += [ctx_]

    for ctx in ctxs:
        if ctx.command:
            old_checks = copy(ctx.command.checks)
            ctx.command.checks = [checks.has_permissions(PermissionLevel.INVALID)]

            await bot.invoke(ctx)

            ctx.command.checks = old_checks
            continue

class Dropdown(discord.ui.Select):
    def __init__(self, bot, msg, thread, config: dict, data: dict, is_home: bool):
        self.bot = bot
        self.msg = msg
        self.thread = thread
        self.config = config
        self.data = data
        self.is_home = is_home
        options = [
            discord.SelectOption(label=line["label"], description=line["description"], emoji=line["emoji"]) for line in data.values()
        ]
        if not is_home:
            options.append(discord.SelectOption(label="Main menu", description="Go back to the main menu", emoji="🏠"))
        super().__init__(placeholder="Select an option to contact the staff team", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            # await interaction.response.send_message("You selected {}".format(self.values[0]))
            await interaction.response.defer()
            await self.view.done()
            if  self.values[0] == "Main menu":
                await self.msg.edit(view=DropdownView(self.bot, self.msg, self.thread, self.config, self.config["options"], True))
            elif self.data[self.values[0]]["type"] == "command":
                await invoke_commands(self.data[self.values[0]]["callback"], self.bot, self.thread, self.thread._genesis_message)
            else:
                await self.msg.edit(view=DropdownView(self.bot, self.msg, self.thread, self.config, self.config["submenus"][self.data[self.values[0]]["callback"]], False))
        except Exception as e:
                print(traceback.format_exc())

class DropdownView(discord.ui.View):
    def __init__(self, bot, msg: discord.Message, thread, config: dict, options: dict, is_home: bool):
        self.msg = msg
        super().__init__(timeout=20)
        self.add_item(Dropdown(bot, msg, thread, config, options, is_home))

    async def on_timeout(self):
        await self.msg.edit(view=None)
        await self.msg.channel.send("Timed out")

    async def done(self):
        self.stop()
        await self.msg.edit(view=None)

class AdvancedMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config = None

    async def cog_load(self):
        self.config = await self.db.find_one({"_id": "advanced-menu"})
        if self.config is None:
            self.config = {"enabled": False, "options": {}, "submenus": {}}
            await self.update_config()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "advanced-menu"},
            {"$set": self.config},
            upsert=True,
        )

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        if self.config["enabled"] and self.config["options"] != {}:
            dummyMessage = DummyMessage(copy(initial_message))
            dummyMessage.author = self.bot.modmail_guild.me
            dummyMessage.content = "Please select an option."
            msgs, _ = await thread.reply(dummyMessage)
            main_recipient_msg = None

            for m in msgs:
                if m.channel.recipient == thread.recipient:
                    main_recipient_msg = m
                    break

            await main_recipient_msg.edit(view=DropdownView(self.bot, main_recipient_msg, thread, self.config, self.config["options"], True))

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.group(invoke_without_command=True)
    async def advancedmenu(self, ctx):
        """Advanced menu settings."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu.command(name="toggle")
    async def advancedmenu_toggle(self, ctx):
        """Toggle the advanced menu."""
        self.config["enabled"] = not self.config["enabled"]
        await self.update_config()
        await ctx.send(f"Advanced menu is now {'enabled' if self.config['enabled'] else 'disabled'}.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu.command(name="show")
    async def advancedmenu_show(self, ctx):
        """Show the current options of the main menu"""
        if self.config["options"] == {}:
            return await ctx.send("There are no options in the main menu.")
        embed = discord.Embed(title="Main menu", color=discord.Color.blurple())
        for k, v in self.config["options"].items():
            embed.add_field(name=v["label"], value=v["description"], inline=False)
        await ctx.send(embed=embed)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu.group(name="option", invoke_without_command=True)
    async def advancedmenu_option(self, ctx):
        """Advanced menu option settings."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_option.command(name="show")
    async def advancedmenu_option_show(self, ctx, *, option: str):
        """Show the details of an option in the main menu"""
        if option not in self.config["options"]:
            return await ctx.send("That option does not exist.")
        embed = discord.Embed(title=self.config["options"][option]["label"], color=discord.Color.blurple())
        embed.add_field(name="Description", value=self.config["options"][option]["description"], inline=False)
        embed.add_field(name="Emoji", value=self.config["options"][option]["emoji"], inline=False)
        embed.add_field(name="Type", value=self.config["options"][option]["type"], inline=False)
        embed.add_field(name="Command" if self.config["options"][option]["type"] == "command" else "Submenu", value=self.config["options"][option]["callback"], inline=False)
        await ctx.send(embed=embed)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_option.command(name="add")
    async def advancedmenu_option_add(self, ctx):
        """Add an option to the advanced menu."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        def typecheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["command", "submenu"]

        if len(self.config["options"]) >= 25:
            return await ctx.send("You can only have a maximum of 25 options due to discord limitations.")

        await ctx.send("What is the label of the option?")
        label = (await self.bot.wait_for("message", check=check)).content

        if label in self.config["options"]:
            await ctx.send("That option already exists. Use `advancedmenu edit` to edit it.")
            return

        await ctx.send("What is the description of the option?")
        description = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the emoji of the option?")
        emoji = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the type of the option? (command/submenu)")
        type = (await self.bot.wait_for("message", check=typecheck)).content

        if type == "command":
            await ctx.send("What is the command to run for the option?")
        else:
            await ctx.send("What is the label of the submenu for the option?")
        callback = (await self.bot.wait_for("message", check=check)).content

        if type == "submenu" and callback not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist. Use `advancedmenu submenu add` to add it.")

        self.config["options"][label] = {
            "label": label,
            "description": description,
            "emoji": emoji,
            "type": type,
            "callback": callback
        }
        await self.update_config()
        await ctx.send("Option added.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_option.command(name="remove")
    async def advancedmenu_option_remove(self, ctx, *, label):
        """Remove an option from the advanced menu."""
        if label not in self.config["options"]:
            return await ctx.send("That option does not exist.")

        del self.config["options"][label]
        await self.update_config()
        await ctx.send("Option removed.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_option.command(name="edit")
    async def advancedmenu_option_edit(self, ctx, *, label):
        """Edit an option from the advanced menu."""
        if label not in self.config["options"]:
            return await ctx.send("That option does not exist.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        def typecheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["command", "submenu"]

        await ctx.send("What is the new description of the option?")
        self.config["options"][label]["description"] = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the new emoji of the option?")
        self.config["options"][label]["emoji"] = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the new type of the option? (command/submenu)")
        type = (await self.bot.wait_for("message", check=typecheck)).content.lower()

        if type == "command":
            await ctx.send("What is the new command to run for the option?")
        else:
            await ctx.send("What is the new label of the new submenu for the option?")
        callback = (await self.bot.wait_for("message", check=check)).content

        if type == "submenu" and callback not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist. Use `advancedmenu submenu add` to add it.")

        self.config["options"][label]["callback"]

        await self.update_config()
        await ctx.send("Option edited.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu.group(name="submenu", invoke_without_command=True)
    async def advancedmenu_submenu(self, ctx):
        """Advanced menu submenu settings."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu.command(name="create")
    async def advancedmenu_submenu_create(self, ctx, *, label):
        """Create a submenu for the advanced menu."""
        if label in self.config["submenus"]:
            return await ctx.send("That submenu already exists. Please use a unique label or use `advancedmenu submenu delete` to delete it.")

        self.config["submenus"][label] = {}
        await self.update_config()
        await ctx.send("Submenu created.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu.command(name="delete")
    async def advancedmenu_submenu_delete(self, ctx, *, label):
        """Delete a submenu for the advanced menu."""
        if label not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        del self.config["submenus"][label]
        await self.update_config()
        await ctx.send("Submenu deleted.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu.command(name="show")
    async def advancedmenu_submenu_show(self, ctx, *, label):
        """Show the options of a submenu."""
        if label not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        if self.config["submenus"][label] == {}:
            return await ctx.send(f"There are no options in {label}")
        embed = discord.Embed(title=label, color=discord.Color.blurple())
        for v in self.config["submenus"][label].values():
            embed.add_field(name=v["label"], value=v["description"], inline=False)
        await ctx.send(embed=embed)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu.group(name="option", invoke_without_command=True)
    async def advancedmenu_submenu_option(self, ctx):
        """Advanced menu submenu option settings."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu_option.command(name="show")
    async def advancedmenu_submenu_option_show(self, ctx, *, label):
        """Show the details of an option in the submenu"""
        if label not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send("What is the label of the option?")
        option = (await self.bot.wait_for("message", check=check)).content

        if option not in self.config["submenus"][label]:
            return await ctx.send("That option does not exist.")
        embed = discord.Embed(title=self.config["submenus"][label][option]["label"], color=discord.Color.blurple())
        embed.add_field(name="Description", value=self.config["submenus"][label][option]["description"], inline=False)
        embed.add_field(name="Emoji", value=self.config["submenus"][label][option]["emoji"], inline=False)
        embed.add_field(name="Type", value=self.config["submenus"][label][option]["type"], inline=False)
        embed.add_field(name="Command" if self.config["submenus"][label][option]["type"] == "command" else "Submenu", value=self.config["submenus"][label][option]["callback"], inline=False)
        await ctx.send(embed=embed)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu_option.command(name="add")
    async def advancedmenu_submenu_option_add(self, ctx, *, submenu: str):
        """Add an option to the advanced submenu."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        def typecheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["command", "submenu"]

        if submenu not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        if len(self.config["submenus"][submenu]) >= 24:
            return await ctx.send("You can only have a maximum of 24 options due to discord limitations.")

        await ctx.send("What is the label of the option?")
        label = (await self.bot.wait_for("message", check=check)).content

        if label == "Main menu":
            return await ctx.send("You cannot use that label.")

        if label in self.config["submenus"][submenu]:
            await ctx.send("That option already exists. Use `advancedmenu submenu edit` to edit it.")
            return

        await ctx.send("What is the description of the option?")
        description = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the emoji of the option?")
        emoji = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the type for the option? (command/submenu)")
        type = (await self.bot.wait_for("message", check=typecheck)).content.lower()

        if type == "command":
            await ctx.send("What is the command to run for the option?")
        else:
            await ctx.send("What is the label of the submenu for the option?")
        callback = (await self.bot.wait_for("message", check=check)).content

        if type == "submenu" and callback not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist. Use `advancedmenu submenu add` to add it.")

        self.config["submenus"][submenu][label] = {
            "label": label,
            "description": description,
            "emoji": emoji,
            "type": type,
            "callback": callback
        }
        await self.update_config()
        await ctx.send("Option added.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu_option.command(name="remove")
    async def advancedmenu_submenu_option_remove(self, ctx, *, submenu: str):
        """Remove an option from the advanced submenu."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        await ctx.send("What is the label of the option to remove?")
        label = (await self.bot.wait_for("message", check=check)).content

        if label not in self.config["submenus"][submenu]:
            return await ctx.send("That option does not exist.")

        del self.config["submenus"][submenu][label]
        await self.update_config()
        await ctx.send("Option removed.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @advancedmenu_submenu_option.command(name="edit")
    async def advancedmenu_submenu_option_edit(self, ctx, *, submenu: str):
        """Edit an option from the advanced submenu."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        def typecheck(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["command", "submenu"]

        if submenu not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        await ctx.send("What is the label of the option to edit?")
        label = (await self.bot.wait_for("message", check=check)).content

        if label not in self.config["submenus"][submenu]:
            return await ctx.send("That label does not exist.")

        await ctx.send("What is the new description of the option?")
        self.config["submenus"][submenu][label]["description"] = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the new emoji of the option?")
        self.config["submenus"][submenu][label]["emoji"] = (await self.bot.wait_for("message", check=check)).content

        await ctx.send("What is the new type for the option? (command/submenu)")
        type = (await self.bot.wait_for("message", check=typecheck)).content.lower()

        self.config["submenus"][submenu][label]["type"] = type
        if type == "command":
            await ctx.send("What is the command to run for the option?")
        else:
            await ctx.send("What is the label of the submenu for the option?")
        callback = (await self.bot.wait_for("message", check=check)).content

        if type == "submenu" and callback not in self.config["submenus"]:
            return await ctx.send("That submenu does not exist.")

        self.config["submenus"][submenu][label]["callback"] = callback

        await self.update_config()
        await ctx.send("Option edited.")

async def setup(bot):
    await bot.add_cog(AdvancedMenu(bot))