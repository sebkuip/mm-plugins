import discord
from discord.ext import commands

from io import BytesIO
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
        image_bytes: BytesIO = BytesIO(await attachment.read())
        image: Image.Image = Image.open(image_bytes)
        flipped_image: Image.Image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        to_send_bytes: BytesIO = BytesIO()
        flipped_image.save(to_send_bytes, format="PNG")
        to_send_bytes.seek(0)
        await ctx.send(file=discord.File(to_send_bytes, filename="flipped.png"))

async def setup(bot):
    await bot.add_cog(ImgFlipper(bot))