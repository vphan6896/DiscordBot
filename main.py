import json
import discord
from discord.ext import commands, tasks
import youtube_dl
import sys

youtube_dl.utils.bug_reports_message = lambda: ''

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

ytdl_format_options = {
    'outtmpl': './playlist/%(title)s.%(ext)s',
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'progress_hooks': [my_hook],
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.2):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            count = 0
            for i in data['entries']:
                print("Entry {}: {}".format(count, i['title']))
                count = count + 1
            # take first item from a playlist
            data = data['entries'][0]
            
            
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

secretFile = open("discordSecret", "r")
clientID = secretFile.readline()
secret = secretFile.readline()
token = secretFile.readline()
secretFile.close()


#Attempt for custom activity message... Not working
#intents = discord.Intents().all()
#activityStatus=discord.Activity(name="Vybing", type=discord.ActivityType.custom)
#client = discord.Client(intents=intents,activity=activityStatus)
bot = commands.Bot(command_prefix='?', self_deaf=True)


class MusicBot(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.playlist = {"0":"Chicken Nugget"}


    @bot.event
    async def on_ready():
        game = discord.Game("by Vybing")
        #Supposedly, Discord likely to disconnect bot if change_presence is used. Alternative is to have constructor
        await bot.change_presence(activity=game)
        print("The bot is ready!")

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("こんにちは!")

    @commands.command(name='join', help='Tells the bot to join the voice channel')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()
        await ctx.message.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)


    @commands.command(name='leave', help='To make the bot leave the voice channel')
    async def leave(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("Leave: The bot is not connected to a voice channel.")

    #Use *url to accept multiple arguments ("chicken attack" otherwise would only search for "chicken" video)
    @commands.command(name='play', help='To play song')
    async def play(self, ctx,*url):
        try :
            server = ctx.message.guild
            voice_channel = server.voice_client
            #SONG CURRENTLY PLAYING
            if ctx.voice_client.is_playing() is True:
                ctx.send("Queueing system coming soon!")
            async with ctx.typing():
                url = ''.join(url)
                filename = await YTDLSource.from_url(url, loop=bot.loop)
                #Good place to queue playlist
                voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
            #Remove file extension from message
            friendlyFileName = filename.strip("playlist\\")
            friendlyFileName = friendlyFileName.split('.')[0]
            friendlyFileName = friendlyFileName.replace("_"," ")
            await ctx.send('**Now playing:** {}'.format(friendlyFileName))
        except:
            await ctx.send("Playing: The bot is not connected to a voice channel.")
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    @commands.command(name='queue', help='Lists song queue')
    async def queue(self, ctx):
        msg = "Queue:\n"
        for key in self.playlist:
            msg += key + ": " + self.playlist[key] + "\n"
        await ctx.send(msg)

    @commands.command(name='pause', help='This command pauses the song')
    async def pause(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("Pausing: The bot is not playing anything at the moment.")
        
    @commands.command(name='resume', help='Resumes the song')
    async def resume(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play command")

    @commands.command(name='stop', help='Stops the song')
    async def stop(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
        else:
            await ctx.send("Stopping: The bot is not playing anything at the moment.")

bot.add_cog(MusicBot(bot))
bot.run(token)