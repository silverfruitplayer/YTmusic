import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import os
import subprocess

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ffmpeg_path = '/usr/bin/ffmpeg'  #Replace.. this was for.. uh.. cloud shell.. run which ffmpeg first plox
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'ffmpeg_location': ffmpeg_path,
    'outtmpl': 'downloads/%(title)s.%(ext)s'
}

os.makedirs("downloads", exist_ok=True)

def check_and_install_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("FFmpeg is already installed.")
        subprocess.run(["pip3", "show", "yt-dlp"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ytdl is already installed.")
        subprocess.run(["pip3", "show", "discord.py"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("discord is already installed.")
        
    except FileNotFoundError:
        print("FFmpeg not installed. Attempting to install...") 
        try:
            # Install ffmpeg using apt
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
            print("FFmpeg installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing FFmpeg: {e}")
            sys.exit("Exiting due to missing FFmpeg installation.")


@bot.event
async def on_ready():
    print(f"Furina Music Bot is online as {bot.user}")
    print("Let the symphony of Hydro elegance begin!")

@bot.command()
async def start(ctx):
    """Send a welcome message with Furina's theme and embed."""
    furina_image_url = "https://i.ibb.co/PYzMyqn/cce8303b880e70a04016b0e91116fe76.jpg"
    embed = discord.Embed(
        title="Furina's Music Bot",
        description=(
            "Welcome to Furina's grand music court! \n"
            "Summon me with your favorite songs, and I shall play them with elegance! 💫\n\n"
            "**Commands to try:**\n"
            "`!song` - Play a song or add it to the queue.\n"
        ),
        color=discord.Color.blue(),
    )
    embed.set_footer(text="Furina is ready to serve!")

    await ctx.send(furina_image_url)
    await asyncio.sleep(0.1)
    await ctx.send(embed=embed)



@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("Furina graces your voice channel! Let the melodies commence!")
    else:
        await ctx.send("Hydro Archon insists: join a voice channel first!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Furina has departed the voice channel, and the queue has been cleared. A dramatic exit!")
    else:
        await ctx.send("Furina isn't even in a voice channel! Such accusations!")

async def play_song(ctx, song_info):
    """Helper function to play a song."""
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.invoke(join)

    try:
        filepath = song_info['filepath']
        source = discord.FFmpegPCMAudio(filepath, executable=ffmpeg_path)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        
        # Furina-styled embed for now playing
        embed = discord.Embed(
            title=f"Now Playing: {song_info['title']}",
            description="Yoohoo! It's time for a Hydro Archon-approved masterpiece!",
            color=0x1E90FF  # Furina's aesthetic Hydro color
        )
        embed.set_thumbnail(url=song_info.get('thumbnail', '')) 
        embed.set_footer(text="Conducted by Furina herself ")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred")
        print(e)

def create_song_embed(title, thumbnail_url):
    """Creates an embed message for the currently playing song."""
    embed = discord.Embed(
        title="Now Playing",
        description=f"**{title}**",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Enjoy Furina's music court!")
    return embed


@bot.command()
async def song(ctx, *, query: str):
    if not ctx.voice_client:
        await ctx.invoke(join)

    voice_client = ctx.voice_client
    if not voice_client:
        return

    await ctx.send(f"Furina is searching for **{query}**, please wait...")

    try:
        search_url = f"ytsearch:{query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            first_result = info["entries"][0]
            title = first_result["title"]
            thumbnail = first_result["thumbnail"]
            filesize = first_result.get("filesize", first_result.get("filesize_approx", 0)) 

            if filesize > 20 * 1024 * 1024:
                await ctx.send(
                    f"Furina cannot download **{title}** because the file exceeds 20MB. Please try a shorter song!"
                )
                return

            filepath = ydl.prepare_filename(first_result).replace('.webm', '.mp3')

            if not os.path.exists(filepath):
                ydl.download([first_result["webpage_url"]])

            source = discord.FFmpegPCMAudio(filepath, executable=ffmpeg_path)
            voice_client.play(source, after=lambda e: print(f"Finished playing: {e}"))

            await ctx.send(f"Now playing: **{title}**", embed=create_song_embed(title, thumbnail))
    except Exception as e:
        await ctx.send(f"An error occurred")
        print(e)


@bot.command()
async def stop(ctx):
    """Stop the current playback."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")
    else:
        await ctx.send("No audio is playing.")

@bot.command()
async def pause(ctx):
    """Pause the current song with Furina's elegant touch."""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = discord.Embed(
            title="Song Paused",
            description="Furina has gracefully paused the music. Shall we resume the melody when you're ready?",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url="https://i.ibb.co/PYzMyqn/cce8303b880e70a04016b0e91116fe76.jpg")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Music Playing",
            description="Furina raises an eyebrow. *“No music? What exactly am I supposed to pause?”*",
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url="https://i.ibb.co/PYzMyqn/cce8303b880e70a04016b0e91116fe76.jpg")  
        await ctx.send(embed=embed)

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        embed = discord.Embed(
            title="Song Resumed",
            description="Furina claps her hands. *“Ah, the melody resumes! Let’s keep the ambiance lively!”*",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url="")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Song Paused",
            description="Furina tilts her head. *“You can’t resume what isn’t paused. Perhaps you need my guidance?”*",
            color=discord.Color.red(),
        )
        embed.set_thumbnail(url="")
        await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"An error occurred: {error}. Furina is deeply troubled!")


if __name__ == "__main__":
    check_and_install_ffmpeg()
    bot.run('TOKEN?')


