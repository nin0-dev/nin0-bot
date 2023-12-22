import discord
from discord.ext import commands
from datetime import timedelta
from discord.ext import bridge
from datetime import datetime
import yaml
from durations import Duration

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    cfg = open('configuration.yaml', 'r')
    config = yaml.safe_load(cfg)

    @bridge.bridge_command(description="Change someone's nickname.")
    @bridge.has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member:discord.Member, nick:str):
        await member.edit(nick=nick)
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: Success")
        successembed.description = member.mention + "'s nickname was changed to `" + nick + "`."
        if ctx.is_app: await ctx.respond(embed=successembed)
        else: await ctx.respond(embed=successembed, mention_author=False)

    def parsevars(self, initial: str, author: discord.Member, member: discord.Member, reason: str, duration: datetime = None):
        result = initial
        result = result.replace('[guild.name]', member.guild.name)
        result = result.replace('[guild.id]', str(member.guild.id))
        result = result.replace('[author.username]', author.name)
        result = result.replace('[author.id]', str(author.id))
        result = result.replace('[author.mention]', author.mention)
        if reason != None: result = result.replace('[punishment.reason]', reason)
        if duration != None: 
            result = result.replace('[punishment.expiresin]', '<t:' + str(int(datetime.timestamp(duration))) + ':R>')
        else:
            result = result.replace('[punishment.expiresin]', 'never')
        return result

    @bridge.bridge_command(description="View someone's user information.")
    async def userinfo(self, ctx, member:discord.Member=None):
        target = ""
        if member == None:
            # user wants to info themselves
            target = ctx.author
        else:
            # user wants to info other
            target = member
        # get user status
        status = ""
        color = 0xffffff
        if target.status == discord.Status.online:
            status = "🟢"
            color = 0x00d26a
        if target.status == discord.Status.idle:
            status = "🟡"
            color = 0xfcd53f
        if target.status == discord.Status.do_not_disturb:
            status = "⛔"
            color = 0xf8312f
        if target.status == discord.Status.invisible:
            status = "⚪️"
        if target.status == discord.Status.streaming:
            status = "🟣"
            color = 0x8d65c5

        # get user info
        username = target.display_name
        createddate = str(int(datetime.timestamp(target.created_at)))
        joineddate = str(int(datetime.timestamp(target.joined_at)))
        # get rpc
        rpcs = ""
        for activity in target.activities:
            if activity.type == discord.ActivityType.playing:
                rpcs = rpcs + "Playing " + activity.name + "\n"
            if activity.type == discord.ActivityType.listening:
                rpcs = rpcs + "Listening to [" + activity.title + " by " + activity.artist + "](" + activity.track_url + ")" + "\n"
            if activity.type == discord.ActivityType.watching:
                rpcs = rpcs + "Watching " + activity.name + "\n"
            if activity.type == discord.ActivityType.streaming:
                rpcs = rpcs + "Streaming at " + activity.twitch_name + "\n"

        infoembed = discord.Embed(color=color, title=status + " " + username)
        infoembed.description = "Created on <t:" + createddate + ":f> (<t:" + createddate + ":R>)\n" + "Joined on <t:" + joineddate + ":f> (<t:" + joineddate + ":R>)"
        if rpcs != "":
            infoembed.add_field(name="Presence info", value=rpcs)
        if ctx.is_app: await ctx.respond(embed=infoembed)
        else: await ctx.respond(embed=infoembed, mention_author=False)
    
    @bridge.bridge_command(description="Set channel/thread slowmode.")
    @bridge.has_permissions(moderate_members=True)
    async def slowmode(self, ctx, seconds:int):
        await ctx.channel.edit(slowmode_delay=seconds)
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: Success")
        successembed.description = "Channel slowmode set to " + str(seconds) + " seconds."
        if ctx.is_app: await ctx.respond(embed=successembed)
        else: await ctx.respond(embed=successembed, mention_author=False)

    @bridge.bridge_command(description="Mute someone.")
    @bridge.has_permissions(moderate_members=True)
    async def mute(self, ctx, member:discord.Member, duration:str, reason:str = "No reason provided"):
        # prep
        await ctx.defer()
        time = datetime.now() + timedelta(seconds=Duration(duration).to_seconds())
        # make DM embed
        dmembed = discord.Embed(color=0xff7d50, title=":mute: You got muted")
        basemsg = self.config["mod"]["dm_punish_messages"]["mute"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason, time)
        # make response embed
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User muted")
        successembed.description = member.mention + " has been muted from this server."
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        successembed.description = successembed.description + "\n> **Expires:** " + "<t:" + str(int(datetime.timestamp(time))) + ":R>"

        # send DM
        if self.config["mod"]["dm_on_punish"]:
            try:
                await member.send(embed=dmembed)
            except:
                successembed.add_field(name="Errors", value="Couldn't send notify DM to user.")
        # timeout
        await member.timeout_for(duration=timedelta(seconds=Duration(duration).to_seconds()), reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason) 
        # send response
        if ctx.is_app:
            if self.config["mod"]["hide_command_author"]:
                await ctx.respond(embed=successembed, ephemeral=True)
            else:
                await ctx.respond(embed=successembed)
        else:
            if self.config["mod"]["hide_command_author"]:
                await ctx.message.delete()
                await ctx.respond(embed=successembed, mention_author=False)
            else:
                await ctx.respond(embed=successembed, mention_author=False)

    @bridge.bridge_command(description="Unmute someone.")
    @bridge.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member:discord.Member, reason:str = "No reason provided"):
        # prep
        await ctx.defer()
        # make DM embed
        dmembed = discord.Embed(color=0x7cff7f, title=":loud_sound: You got unmuted")
        basemsg = self.config["mod"]["dm_punish_messages"]["unmute"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason)
        # make response embed
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User unmuted")
        successembed.description = member.mention + " has been unmuted from this server."
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        # send DM
        if self.config["mod"]["dm_on_punish"]:
            try:
                await member.send(embed=dmembed)
            except:
                successembed.add_field(name="Errors", value="Couldn't send notify DM to user.")
        # unmute
        await member.remove_timeout(reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason)
        # send response
        if ctx.is_app:
            if self.config["mod"]["hide_command_author"]:
                await ctx.respond(embed=successembed, ephemeral=True)
            else:
                await ctx.respond(embed=successembed)
        else:
            if self.config["mod"]["hide_command_author"]:
                await ctx.message.delete()
                await ctx.respond(embed=successembed, mention_author=False)
            else:
                await ctx.respond(embed=successembed, mention_author=False)

    @bridge.bridge_command(description="Kick someone.")
    @bridge.has_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, reason:str = "No reason provided"):
        # kick
        await ctx.defer()
        # make DM embed
        dmembed = discord.Embed(color=0xff5050, title=":door: You got kicked")
        basemsg = self.config["mod"]["dm_punish_messages"]["kick"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason)
        # make response embed
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User kicked")
        successembed.description = member.mention + " has been kicked from this server."
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        # send DM
        if self.config["mod"]["dm_on_punish"]:
            try:
                await member.send(embed=dmembed)
            except:
                successembed.add_field(name="Errors", value="Couldn't send notify DM to user.")
        # kick
        await member.kick(reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason)
        # send response
        if ctx.is_app:
            if self.config["mod"]["hide_command_author"]:
                await ctx.respond(embed=successembed, ephemeral=True)
            else:
                await ctx.respond(embed=successembed)
        else:
            if self.config["mod"]["hide_command_author"]:
                await ctx.message.delete()
                await ctx.respond(embed=successembed, mention_author=False)
            else:
                await ctx.respond(embed=successembed, mention_author=False)
        
    @bridge.bridge_command(description="Ban someone.")
    @bridge.has_permissions(kick_members=True)
    async def ban(self, ctx, member:discord.Member, reason:str = "No reason provided", delete_days: int = config["mod"]["ban_msgdelete_days"]):
        # prep
        await ctx.defer()
        # make DM embed
        dmembed = discord.Embed(color=0xff5050, title=":hammer: You got banned")
        basemsg = self.config["mod"]["dm_punish_messages"]["ban"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason)
        # make response embed   
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User banned")
        successembed.description = member.mention + " has been banned from this server."
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        if delete_days != 0: successembed.description = successembed.description + "\n> **Messages deleted:** " + str(delete_days) + " days"
        # send DM
        if self.config["mod"]["dm_on_punish"]:
            try:
                await member.send(embed=dmembed)
            except:
                successembed.add_field(name="Errors", value="Couldn't send notify DM to user.")
        # ban
        await member.ban(reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason, delete_message_seconds=delete_days*86400)
        # send response
        if ctx.is_app:
            if self.config["mod"]["hide_command_author"]:
                await ctx.respond(embed=successembed, ephemeral=True)
            else:
                await ctx.respond(embed=successembed)
        else:
            if self.config["mod"]["hide_command_author"]:
                await ctx.message.delete()
                await ctx.respond(embed=successembed, mention_author=False)
            else:
                await ctx.respond(embed=successembed, mention_author=False)

    @bridge.bridge_command(description="Unban someone.")
    @bridge.has_permissions(ban_members=True)
    async def unban(self, ctx, userid:str, reason:str = "No reason provided"):
        # prep
        await ctx.defer()
        user = await self.bot.fetch_user(int(userid))
        # make response embed   
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User unbanned")
        successembed.description = user.mention + " has been unbanned from this server."
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        # ban
        await ctx.guild.unban(user, reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason)
        # send response
        if ctx.is_app:
            if self.config["mod"]["hide_command_author"]:
                await ctx.respond(embed=successembed, ephemeral=True)
            else:
                await ctx.respond(embed=successembed)
        else:
            if self.config["mod"]["hide_command_author"]:
                await ctx.message.delete()
                await ctx.respond(embed=successembed, mention_author=False)
            else:
                await ctx.respond(embed=successembed, mention_author=False)
        

def setup(bot): 
    bot.add_cog(Mod(bot))