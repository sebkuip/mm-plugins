import discord
from discord.ext import commands

from PIL import Image

class ImgFlipper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def imgflip(self, ctx: commands.Context):
        """Flip an image horizontally"""
        if not ctx.message.attachments:
            await ctx.send("You need to attach an image!")
            return
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not attachment.content_type.startswith("image/"):
            await ctx.send("You need to attach an image!")
            return
        image_bytes: bytes = await attachment.read()
        image: Image.Image = Image.frombytes("RGBA", (attachment.height, attachment.width), image_bytes)
        flipped_image: Image.Image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        await ctx.send(file=discord.File(flipped_image.tobytes(), filename="flipped.png"))

async def setup(bot):
    await bot.add_cog(ImgFlipper(bot))