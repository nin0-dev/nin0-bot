# a skeleton cog you can use to make cogs
import discord
from discord.ext import commands
import yaml

class OneGuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    cfg = open('configuration.yaml', 'r')
    config = yaml.safe_load(cfg)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if config["guild_id"] == guild.id:
            await guild.leave()

        
def setup(bot): 
    bot.add_cog(OneGuild(bot))