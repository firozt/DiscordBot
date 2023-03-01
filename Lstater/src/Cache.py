import json


class CachedGameElement(object):
    
    def __init__(self, match_id, kda, won) -> None:
        self.match_id = match_id
        self.kda = kda
        self.won = won
        
class Cache(object):
    
    def __init__(self, puuid) -> None:
        self.cache_stack = [] # stores matches in a stack datastructure
        self.puuid = puuid
    
    def addGameToCache(self, match_id,kda, won) -> None:
        """Adds given game to the cache stack

        Args:
            kda (float): kills + assists / death
            won (bool): boolean to represent win or loss
        """
        
        self.cache_stack.append(CachedGameElement(match_id,kda,won))
        
    
    def getFromCache(self,match_id) -> CachedGameElement:
        for cached_match in self.cache_stack:
            if cached_match.match_id == match_id:
                return cached_match
        return None

    
def cacheToJson(cacheObj: Cache) -> str:
    cache_stack_arr = [] 
    for match in cacheObj.cache_stack:
        cache_stack_arr.append(
            {
                'match_id' : match.match_id,
                'kda' : match.kda,
                'won' : match.won,
            }
        )
    dict = {
        'puuid' : cacheObj.puuid,
        'cache_stack' : cache_stack_arr,
    }
    
    return json.dumps(dict)

def jsonToCache(data):
    data = json.loads(data)
    print(data)