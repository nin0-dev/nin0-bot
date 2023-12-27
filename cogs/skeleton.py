# a skeleton cog you can use to make cogs
import discord
from discord.ext import commands

class CogName(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    group = discord.SlashCommandGroup("group", "_____ commands.")

        
def setup(bot): 
    bot.add_cog(CogName(bot))