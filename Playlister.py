# bot.py
import os
import discord
import re
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.transport.requests

from pathlib import Path
from dotenv import load_dotenv

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
re_pat_song_url = re.compile(r'^\*\*\[(.*)\]\((?:https?:\/{2})?(?:w{3}\.)?youtu(?:be)?\.(?:com|be)(?:\/watch\?v=|\/)([^\s&]+)\)\*\*$')
youtube = None
playlistId = None # the ID of the playlist on YouTube


client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

# TODO: verify this helps
def refresh_execute(request):
    if request.http.credentials.expired:
        refresh_request = google.auth.transport.requests.Request()
        request.http.credentials.refresh(refresh_request)
        print("Refreshed Token!")
    return request.execute()

@client.event
async def on_message(message):
    global youtube
    if message.author.id == 235_088_799_074_484_224 and len(message.embeds):
        for embed in message.embeds:
            if embed.author.name == 'Added to queue':
                match = re.fullmatch(re_pat_song_url, embed.description)
                print(embed.description)
                video_name = match.group(1)
                video_id   = match.group(2)
                print(f'videoId: {video_id!r}')

                # check if the video is in the playlist
                request = youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        maxResults=1,
                        playlistId=playlistId,
                        videoId=video_id
                    )

                response = refresh_execute(request)
                # if there are results, it's already in the playlist.
                if response['pageInfo']['totalResults']:
                    msg = f':information_source: `{video_name}` is already in **The Fam: Music Jam**.'

                # else add it to the playlist
                else:
                    request = youtube.playlistItems().insert(
                            part="snippet",
                            body={
                              "snippet": {
                                "playlistId": playlistId,
                                "position"  : 0,
                                "resourceId": {
                                    "kind"   : "youtube#video",
                                    "videoId": video_id
                                }
                              }
                            }
                        )

                    refresh_execute(request)

                    msg = f':white_check_mark: I added `{video_name}` to **The Fam: Music Jam**!'

                print(msg)
                await message.channel.send(msg)


def main():
    global youtube
    env_path = Path('..') / '.env'
    load_dotenv(dotenv_path=env_path)
    TOKEN = os.getenv('DISCORD_TOKEN')
    playlistId = os.getenv('PLAYLIST_ID')

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "../client_secret_697711587569-5cddr879kf793qdvfnm6c396cch2cdrs.apps.googleusercontent.com.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    client.run(TOKEN)


if __name__ == "__main__":
    main()
