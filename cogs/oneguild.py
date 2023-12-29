# a skeleton cog you can use to make cogs
import discord
from discord.ext import commands

class OneGuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await guild.leave()

        
def setup(bot): 
    bot.add_cog(OneGuild(bot))