import sys, os
import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv

regions = {
    'euw1':'europe',
    'na1':'north-america'
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!',intents=intents)

def run_bot():
    @bot.event
    async def on_ready():
        print('bot is running')
    load_dotenv()
    bot.run(os.getenv('TOKEN'))



@bot.command()
async def stop(ctx):
    await sys.exit(0)

@bot.command()
async def winrate(ctx,summoner_name ,region='euw1'):
    """gets the winrate of a given player in a given region

    Args:
        ctx (message): discord context variable
        summoner_name (str): username of the summoner
        region (str, optional): region of the. Defaults to 'euw1'.
    """
    
    PUUID = await getPUUID(summoner_name,region=region)
    if PUUID == -1:
        await ctx.send(f'Invalid username or region')
        return
    matchIdHistory = await getMatchIDHistory(region,PUUID,start_index=0,number_of_matches=20)
    if  matchIdHistory == -1:
        await ctx.send(f'Error getting match history')
        return

    total_games, won_games = 0, 0
    for matchID in matchIdHistory:
        total_games += 1
        if await wonGame(region, matchID, PUUID):
            won_games += 1
    winrate = (won_games / total_games) * 100
    await ctx.send(f'Your winrate is {winrate:.2f}')
    
async def getPUUID(summoner_name,region) -> str:
    """gets PUUID given a league username and region

    Args:
        summoner_name (str): username of the player
        region (str): which servers used i.e euw1, na1

    Returns:
        str: _description_
    """
    
    request_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={os.getenv("RIOT_API_KEY")}'
    response = requests.get(request_url)
    if response.status_code != 200:
        return -1
    
    return response.json()["puuid"]
    
async def getMatchIDHistory(region,PUUID,start_index,number_of_matches) -> list[str]:
    """Returns a players last n matchID's

    Args:
        region (str): which servers i.e euw1, na1
        PUUID (str): riot account id
        start_index (int): which game number to start
        number_of_matches (int): number of matches since start_index

    Returns:
        list[str]: list of match ids 
    """
   
    request_url = f'https://{regions[region]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{PUUID}/ids?start={start_index}&count={number_of_matches}&api_key={os.getenv("RIOT_API_KEY")}'
    response = requests.get(request_url)
    if str(response.status_code)[0] == '4':
        return -1
    return response.json()
    
async def wonGame(region, match_id, PUUID) -> bool:
    """Returns wether given a player and match if he won

    Args:
        region (str): which riot server i.e euw1, na1
        match_id (str): id of match
        PUUID (str): riot account id

    Returns:
        bool: true = won, false = lost
    """

    request_url = f'https://{regions[region]}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={os.getenv("RIOT_API_KEY")}'
    response = requests.get(request_url)
    if str(response.status_code)[0] == '4':
        return -1
    user_stats = response.json()['info']['participants']

    for user in user_stats:
        if user['puuid'] == PUUID:
            return user['win']
    print('CAN NOT FIND USER IN MATCH')
    sys.exit(1)
