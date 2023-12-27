import discord
from discord.ext import commands
from datetime import timedelta
from discord.ext import bridge
from datetime import datetime
import yaml
from durations import Duration

class Case:
    def __init__(self, caseid, target, mod, reason, type, time):
        self.caseid = caseid
        self.target = target
        self.mod = mod
        self.reason = reason
        self.type = type
        self.time = time

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    cfg = open('configuration.yaml', 'r')
    config = yaml.safe_load(cfg)


    def get_case(self, cid: int):
        casesfile = open('data/cases.yaml', 'r')
        cases = yaml.safe_load(casesfile)
        caseid = 0
        try:
            caseid = cases[cid]
        except:
            raise Exception("Case doesn't exist")
        target = cases[cid]["user"]
        moderator = cases[cid]["moderator"]
        reason = cases[cid]["reason"]
        ctype = cases[cid]["type"]
        time = cases[cid]["time"]
        return Case(cid, target, moderator, reason, ctype, time)

    def create_case(self, target, moderator, reason, ctype, time):
        with open("data/cases.yaml", "r") as file:
            cases = yaml.safe_load(file)
            if cases is None: cases = {}
            casescount = len(cases)
            newcasename = casescount + 1
            newcasedata = {"user": target, "moderator": moderator, "reason": reason, "type": ctype, "time": time} 
            cases[newcasename] = newcasedata
        with open("data/cases.yaml", "w") as file:
            yaml.dump(cases, file, default_style='"')
        return int(newcasename)

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
        # make case
        cid = self.create_case(member.id, ctx.author.id, reason, "mute", int(datetime.timestamp(time)))
        # make DM embed
        dmembed = discord.Embed(color=0xff7d50, title=":mute: You got muted")
        basemsg = self.config["mod"]["dm_punish_messages"]["mute"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason, time)
        # make response embed
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User muted")
        successembed.description = member.mention + " has been muted from this server."
        successembed.description = successembed.description + "\n> **Case ID:** `" + str(cid) + "`"
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason)
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
        # make case
        cid = self.create_case(member.id, ctx.author.id, reason, "kick", int(datetime.timestamp(time)))
        # make DM embed
        dmembed = discord.Embed(color=0xff5050, title=":door: You got kicked")
        basemsg = self.config["mod"]["dm_punish_messages"]["kick"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason)
        # make response embed
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User kicked")
        successembed.description = member.mention + " has been kicked from this server."
        successembed.description = successembed.description + "\n> **Case ID:** `" + str(cid) + "`"
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
        # make case
        cid = self.create_case(member.id, ctx.author.id, reason, "ban", int(datetime.timestamp(time)))
        # make DM embed
        dmembed = discord.Embed(color=0xff5050, title=":hammer: You got banned")
        basemsg = self.config["mod"]["dm_punish_messages"]["ban"]
        dmembed.description = self.parsevars(basemsg, ctx.author, member, reason)
        # make response embed   
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User banned")
        successembed.description = member.mention + " has been banned from this server."
        successembed.description = successembed.description + "\n> **Case ID:** `" + str(cid) + "`"
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

    @bridge.bridge_command(description="Ban someone that isn't in the server.")
    @bridge.has_permissions(ban_members=True)
    async def hackban(self, ctx, userid:str, reason:str = "No reason provided", delete_days: int = config["mod"]["ban_msgdelete_days"]):
        # prep
        await ctx.defer()
        user = await self.bot.fetch_user(int(userid))
        # make case
        cid = self.create_case(user.id, ctx.author.id, reason, "ban", int(datetime.timestamp(time)))
        # make response embed   
        successembed = discord.Embed(color=0x7cff7f, title=":white_check_mark: User banned")
        successembed.description = user.mention + " has been banned from this server."
        successembed.description = successembed.description + "\n> **Case ID:** `" + str(cid) + "`"
        if reason != None: successembed.description = successembed.description + "\n> **Reason:** " + str(reason) + ""
        if delete_days != 0: successembed.description = successembed.description + "\n> **Messages deleted:** " + str(delete_days) + " days"
        # add dm error
        if self.config["mod"]["dm_on_punish"]:
            successembed.add_field(name="Errors", value="Couldn't send notify DM to user as they were hack-banned.")
        # ban
        await ctx.guild.ban(user, reason="<" + ctx.author.name + "> (" + str(ctx.author.id) + "): " + reason, delete_message_seconds=delete_days*86400)
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

    @bridge.bridge_command(description="View a moderation case.")
    @bridge.has_permissions(moderate_members=True)
    async def case(self, ctx, caseid:int):
        await ctx.defer()
        # get case
        case = self.get_case(caseid)
        # make response embed
        embed = discord.Embed()
        if case.type == "warn": embed.color = 0xfcd53f
        if case.type == "mute": embed.color = 0xff7d50
        if case.type == "kick": embed.color = 0xff5050
        if case.type == "ban": embed.color = 0xff5050
        embed.title = "Case information"
        embed.description = "> **ID:** `" + str(case.caseid) + "`\n> **User:** <@" + str(case.target) + ">\n> **Moderator:** <@" + str(case.mod) + ">\n> **Type:** " + case.type + "\n> **Reason:** " + case.reason + "\n> **Created at:** <t:" + str(case.time) + ">" 
        if ctx.is_app: await ctx.respond(embed=embed)
        else: await ctx.respond(embed=embed, mention_author=False)

        

def setup(bot): 
    bot.add_cog(Mod(bot))