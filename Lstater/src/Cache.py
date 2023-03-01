
class CachedGameElement(object):
    
    def __init__(self, match_id, kda, won) -> None:
        self.match_id = match_id
        self.kda = kda
        self.won = won
        
class Cache(object):
    
    def __init__(self, puuid) -> None:
        self.last_match_id = None
        self.cache_stack = [] # stores matches in a stack datastructure
        self.puuid = puuid
    
    def addGameToCache(self, match_id, kda, won) -> None:
        """Adds given game to the cache stack

        Args:
            match_id (str): match identifier
            kda (float): kills + assists / death
            won (bool): boolean to represent win or loss
        """
        
        self.cache_stack.append(CachedGameElement(match_id,kda,won))
        self.last_match_id = match_id
        
    
    def getFromCache(self,match_id) -> CachedGameElement:
        for cached_match in self.cache_stack:
            if cached_match.match_id == match_id:
                return cached_match
        return None
    
def cacheToJson(match: CachedGameElement) -> dict:
    return {
        'kda' : match.kda,
        'won' : match.won
    }