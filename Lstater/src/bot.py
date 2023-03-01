import os , requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
import Cache

local_cache = {} # stores name : cache object with users cached values

NUM_OF_REQUEST = 0


players = [
    'roooge',
    'molgera12',
    'newtronimus',
    'kayj0'
]

# v5 api uses continental names whilst v4 uses the old server system
# this dictionary will help convert region names from the v4 system to v5
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

async def loading(ctx):
    await ctx.send('loading...')
    
async def finished_loading(ctx):
    async for m in ctx.channel.history(limit=200):
        if m.author == bot.user and m.content == 'loading...':
            last_message = m
            await last_message.delete()
            return        
    
@bot.command()
async def cache(ctx):
    offload()

@bot.command()
async def load(ctx):
    load()


@bot.command()
async def leaderboard(ctx, filter='winrate'):
    NUM_OF_GAMES = 4
    await loading(ctx)
    # error testing
    if filter not in ['winrate', 'kda']:
        await ctx.send(f'{filter} is not a valid filter!')
        return
    player_list = []
    if filter == 'winrate':
        player_list = await filterWinrate(NUM_OF_GAMES)
    elif filter =='kda':
        player_list = filterKDA()

    i = 1
    medals = {
        1 : ':first_place:',
        2 : ':second_place:',
        3 : ':third_place:',
    }
    await finished_loading(ctx)
    await ctx.send(f'Leaderboards for winrates over {NUM_OF_GAMES} games:\n ')
    for player in player_list:
        out = f'{i}) {player[0]} | winrate: {player[1]}% {str(medals[i]) if i in medals else ""}'
        await ctx.send(out)
        i += 1
    
    request_logs()
    

@bot.command()
async def winrate(ctx,summoner_name, num_of_match = 20, region='euw1'):
    """ input summoner name and returns winrate of n matches

    Args:
        ctx (message): discord context variable
        summoner_name (str): username of the summoner
        num_of_match (int) : (defaults to 20) how far to go back
        region (str, optional): region of the. Defaults to 'euw1'.
    """
    await loading(ctx)
    winrate = await getWinrate(summoner_name, num_of_match, region)
    if winrate < 0:
        await ctx.send(f'Error too many requests sent')
        return
    await finished_loading(ctx)
    await ctx.send(f"{summoner_name}'s winrate is {winrate:.2f}% over {num_of_match} games")
    request_logs()
    
async def filterKDA(summoner_name, region):
    kda = []
    for player in players:
        kda.append((player, await getKDA(player, region)))
    
async def getKDA(name):
    PUUID = await getPUUID(name)
    if PUUID == -1: return -1
    matchHistory = getMatchIDHistory(region,PUUID)

async def filterWinrate(NUM_OF_GAMES) -> list[str]:
    """Returns sorted list of names by winrates

    Returns:
        list[str]: list of sorted names by winrate
    """
    winrate = []
    for player in players:
        winrate.append((player, await getWinrate(player,NUM_OF_GAMES)))
    return sorted(winrate, key=lambda x: x[1], reverse=True)
    
async def getWinrate(summoner_name, num_of_match, region ='euw1'):
    """gets the winrate of a given player in a given region

    Args:
        ctx (message): discord context variable
        summoner_name (str): username of the summoner
        region (str, optional): region of the. Defaults to 'euw1'.
    """
      
    PUUID = await getPUUID(summoner_name,region)
    if PUUID == -1: return -1
    matchIdHistory = await getMatchIDHistory(region,PUUID,start_index=0,number_of_matches=num_of_match)
    if  matchIdHistory == -1: return matchIdHistory

    total_games, won_games = 0, 0
    for matchID in matchIdHistory:
        total_games += 1
        if await wonGame(summoner_name,region, matchID, PUUID):
            won_games += 1
    return (won_games / total_games) * 100

async def getPUUID(summoner_name,region) -> str:
    """gets PUUID given a league username and region

    Args:
        summoner_name (str): username of the player
        region (str): which servers used i.e euw1, na1

    Returns:
        str: _description_
    """
    
    # CHECK IF DATA IS IN CACHE
    
    if summoner_name in local_cache:
        print(f'cache hit for {summoner_name}')
        return local_cache[summoner_name].puuid
        
    
    request_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={os.getenv("RIOT_API_KEY")}'
    response = requests.get(request_url)
    
    if response.status_code != 200:
        return -1
    
    puuid = response.json()["puuid"]
    
    # cache element
    cache_player(summoner_name, puuid)
    increaseReq()
    return puuid
    
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
    increaseReq()
    return response.json()

async def getGameData(summoner_name, region, match_id, PUUID) -> dict:
    """Returns the match object containing info on the user

    Args:
        summoner_name (str) : name of the user
        region (str): which riot server i.e euw1, na1
        match_id (str): id of match
        PUUID (str): riot account id

    Returns:
       dict: kda -> str, won -> bool
    """
    # check cache
    if summoner_name in local_cache:
        
        cache_hit = local_cache[summoner_name].getFromCache(match_id)
        if cache_hit:
            
            print(f'cache hit for match: {match_id} for user: {summoner_name}')
            return Cache.cacheToJson(cache_hit)
            
    # request
    
    request_url = f'https://{regions[region]}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={os.getenv("RIOT_API_KEY")}'
    response = requests.get(request_url)
    if str(response.status_code)[0] == '4':
        return -1
    
    response = response.json()['info']['participants']
    for user in response:
        if user['puuid'] == PUUID:
            response = user
            break
        
    match = {
        'kda' : float(response['challenges']['kda']),
        'won' : bool(response['win']),
    }
    
    cache_game(match_id,summoner_name,match['kda'],match['won'])
    increaseReq()

    return match
    
async def wonGame(summoner_name, region, match_id, PUUID) -> bool:

    match = await getGameData(summoner_name,region,match_id,PUUID)
    return match['won']

# CACHNING FUNCTIONS

def cache_game(match_id,name, kda, won) -> None:
    if name not in local_cache:
        local_cache[name] = Cache.Cache()
        print(f'cache created for {name}')
    local_cache[name].addGameToCache(match_id,kda,won)
    
def cache_player(name, puuid):
    local_cache[name] = Cache.Cache(puuid)

    
def offload() -> None:
    json = '{'
    for player in players:
        json += f'"{player}" : {Cache.cacheToJson(local_cache[player])},'
    json = json[:-1] + '}'
    with open('../request_cache.json', 'w') as f:
        f.write(json)
    f.close()
    
def load() -> None:
    data = ''
    with open('../request_cache.json', 'r') as f:
        for line in f:
            data += f.readline()
    Cache.jsonToCache(data)
    
# DEBUGGING

def request_logs():
    global NUM_OF_REQUEST
    print(f'num of requests: {NUM_OF_REQUEST}')
    NUM_OF_REQUEST = 0

def increaseReq():
    global NUM_OF_REQUEST
    NUM_OF_REQUEST += 1