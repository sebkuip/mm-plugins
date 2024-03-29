import asyncio
import copy
from datetime import datetime

import discord
from discord.channel import CategoryChannel
from discord.ext import commands

from core import checks
from core.models import DummyMessage, PermissionLevel


class Questions(commands.Cog):
    """Reaction-based menu for threads"""
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)

    def user_resp(self, channel, member, *, timeout=15):
        return self.bot.wait_for('message', check=lambda m: getattr(m.channel, 'recipient', m.channel) == channel and m.author == member, timeout=timeout)

    @commands.Cog.listener()
    async def on_thread_ready(self, thread, creator, category, initial_message):
        """Sends out menu to user"""
        config = await self.db.find_one({'_id': 'config'}) or {}
        responses = {}
        if not config.get('questions'): return
        print(config)

        q_message = DummyMessage(copy.copy(initial_message))
        q_message.author = self.bot.modmail_guild.me

        for question in config['questions']:
            print(question)
            q_message.content = question
            await thread.reply(q_message)

            try:
                m = await self.user_resp(thread.recipient, thread.recipient, timeout=15000)
                print(m.content)
            except asyncio.TimeoutError:
                print("timeout")
                await thread.close(closer=self.bot.modmail_guild.me, message='Closed due to inactivity and not responding to questions')
                return
            finally:
                answer = m.content if m.content else "<No Message Content>"
                answer += "\n"
                if len(m.attachments) > 0:
                    for attachment in m.attachments:
                        answer += f"\n`{attachment.filename}`: {attachment.url}"

                responses[question] = answer
            print("looping")

        await asyncio.sleep(1)
        em = discord.Embed(color=self.bot.main_color, timestamp=datetime.utcnow())
        for k, v in responses.items():
            em.add_field(name=k, value=v, inline=False)
        em.set_author(name=m.author.name, icon_url=m.author.avatar_url)
        message = await thread.channel.send(embed=em)
        await message.pin()

        q_message.content = 'Your appeal will now be reviewed by our moderation team. If you have new information to share about this case, please reply to this message.'
        await thread.reply(q_message)

        move_to = self.bot.get_channel(int(config['move_to']))
        print(move_to)
        await thread.channel.edit(category=move_to, sync_permissions=True)

    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command()
    async def configquestions(self, ctx, *, move_to: CategoryChannel):
        """Configures the questions plugin.
        
        `move_to` should be a category to move to after questions answered.
        Initial category should be defined in `main_category_id`
        """
        questions = []
        await ctx.send('How many questions do you have?')
        try:
            m = await self.user_resp(ctx.channel, ctx.author)
        except asyncio.TimeoutError:
            return await ctx.send('Timed out.')
        try:
            count = int(m.content)
        except ValueError:
            return await ctx.send('Invalid input')

        for _ in range(count):
            await ctx.send("What's the question?")
            try:
                m = await self.user_resp(ctx.channel, ctx.author)
            except asyncio.TimeoutError:
                return await ctx.send('Timed out.')
            questions.append(m.content)

        await self.db.find_one_and_update({'_id': 'config'}, {'$set': {'questions': questions, 'move_to': str(move_to.id)}}, upsert=True)
        await ctx.send('Saved')


async def setup(bot):
    await bot.add_cog(Questions(bot))
