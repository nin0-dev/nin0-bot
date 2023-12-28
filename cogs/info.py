import discord
from discord.ext import commands
from datetime import datetime
from discord.ext import bridge



class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @bridge.bridge_command(description="View someone's user information.")
    async def userinfo(self, ctx, member:discord.Member = None):
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
        infoembed.set_thumbnail(url=target.avatar.url)
        if rpcs != "":
            infoembed.add_field(name="Presence info", value=rpcs)
        # get roles
        roles = ""
        for role in target.roles:
            roles = roles + role.mention + ", "
        roles = roles.rstrip(", ")
        infoembed.add_field(name="Roles", value=roles, inline=False)
        if ctx.is_app: await ctx.respond(embed=infoembed)
        else: await ctx.respond(embed=infoembed, mention_author=False)

        
def setup(bot): 
    bot.add_cog(Info(bot))