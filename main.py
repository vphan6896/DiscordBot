import json
import discord
from discord.ext import commands, tasks
import youtube_dl
import sys

secretFile = open("discordSecret", "r")
clientID = secretFile.readline()
secret = secretFile.readline()
token = secretFile.readline()
secretFile.close()


intents = discord.Intents().all()

#activityStatus=discord.Activity(name="Vybing", type=discord.ActivityType.custom)
#client = discord.Client(intents=intents,activity=activityStatus)
bot = commands.Bot(command_prefix='?', self_deaf=True)

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'outtmpl': './playlist/%(title)s-%(id)s.%(ext)s',
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
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


@bot.event
async def on_ready():
    act=discord.Activity(name="Vybing")
    await bot.change_presence(activity=act)
    print("The bot is ready!")

@bot.command()
async def hello(ctx):
    await ctx.send("こんにちは!")

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.message.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)


@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("Leave: The bot is not connected to a voice channel.")


@bot.command(name='play', help='To play song')
async def play(ctx,url):
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        #Remove file extension from message
        friendlyFileName = filename.strip("playlist\")
        friendlyFileName = friendlyFileName.split('.')[0]
        friendlyFileName = friendlyFileName.replace("_"," ")
        await ctx.send('**Now playing:** {}'.format(friendlyFileName))
    except:
        await ctx.send("Playing: The bot is not connected to a voice channel.")
        e = sys.exc_info()[0]
        print("Error: %s" % e)


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("Pausing: The bot is not playing anything at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play command")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("Stopping: The bot is not playing anything at the moment.")

bot.run(token)