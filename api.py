import aiohttp

async def fetch_anime_data(query_or_url: str, api_search_url: str = None):
    """
    Queries the AnimeSalt API or validates direct URLs.
    """
    if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
        filename = query_or_url.split("/")[-1].split("?")[0]
        if not filename or "." not in filename:
            filename = "anime_video.mp4"
            
        return {
            "stream_url": query_or_url,
            "title": "Direct_Link_Video",
            "season": "1",
            "episode": "1",
            "quality": "Unknown",
            "audio": "Sub",
            "synopsis": "Direct file download."
        }

    if not api_search_url:
        api_search_url = f"https://animesalt-api-endpoint-url.com/search?q={query_or_url}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_search_url) as resp:
            if resp.status != 200:
                raise Exception(f"API returned status code {resp.status}")
            
            data = await resp.json()
            result = data.get("results", [{}])[0]
            stream_url = data.get("stream_url") or result.get("url")
            
            if not stream_url:
                raise Exception("No downloadable media found for this query.")
                
            return {
                "stream_url": stream_url,
                "title": result.get("title", query_or_url),
                "season": str(result.get("season", "1")),
                "episode": str(result.get("episode", "1")),
                "quality": result.get("quality", "720p"),
                "audio": result.get("audio", "Sub"),
                "synopsis": result.get("synopsis", "Streamed seamlessly via AnimeSalt API.")
            }
