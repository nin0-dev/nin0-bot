import discord
import os # default module
from discord.ext import bridge
from discord.ext import commands
from dotenv import load_dotenv
from cogs import mod
import yaml

cfg = open('configuration.yaml', 'r')
config = yaml.safe_load(cfg)
load_dotenv() # load all the variables from the env file
intents = discord.Intents.all()
bot = bridge.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    # leave guilds
    for guild in bot.guilds:
        if not guild.id == config["guild_id"]:
            await guild.leave()


cogs_list = [
    'mod',
    'info',
    'oneguild'
]

for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')
    
@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    errorembed = discord.Embed()
    if "403 Forbidden (error code: 50013): Missing Permissions" in str(error): # Bot missing perms
        errorembed = discord.Embed(color=0xffbcbc, title=":x: Bot missing permissions", description="Either:\n- the bot does not have needed permissions;\n- the target is above the bot;\n- the target is the guild owner.")
    else: # other error
        errorembed = discord.Embed(color=0xffbcbc, title=":x: An error occured :(")
        errorembed.description = "Here are the error details: \n```" + str(error) + "```"
    await ctx.respond(embed=errorembed, ephemeral=True)

@bot.event
async def on_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    errorembed = discord.Embed()
    if "403 Forbidden (error code: 50013): Missing Permissions" in str(error): # Bot missing perms
        errorembed = discord.Embed(color=0xffbcbc, title=":x: Bot missing permissions", description="Either:\n- the bot does not have needed permissions;\n- the target is above the bot;\n- the target is the guild owner.")
    if isinstance(error, commands.MissingPermissions):
        errorembed = discord.Embed(color=0xffbcbc, title=":x: No permissions", description="You are not allowed to execute that command.")
    if isinstance(error, commands.CommandNotFound):
        errorembed = discord.Embed(color=0xffbcbc, title=":x: Command not found", description="The command that you tried to use does not exist.")
    else: # other error
        errorembed = discord.Embed(color=0xffbcbc, title=":x: An error occured")
        errorembed.description = "Here are the error details: \n```" + str(error) + "```"
    await ctx.respond(embed=errorembed, mention_author=False)
    
# check oneguild
if config["guild_id"] == "YOUR_SERVER_ID":
    print("ERROR: Please set your guild id in configuration.yaml.")
    exit(1)
bot.run(os.getenv('TOKEN')) # run the bot with the token of
