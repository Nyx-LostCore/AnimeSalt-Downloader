# api.py
import aiohttp

async def fetch_anime_data(query_or_url: str, base_api_url: str = None):
    """
    Queries the AnimeSalt API using the correct /api/search?q={query} route.
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

    if not base_api_url:
        base_api_url = "https://animesalt-api-lovat.vercel.app"
    
    base_api_url = base_api_url.rstrip("/")
    api_search_url = f"{base_api_url}/api/search?q={query_or_url}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_search_url) as resp:
            if resp.status != 200:
                raise Exception(f"API returned status code {resp.status}")
            
            data = await resp.json()
            results = data.get("results") or data.get("data") or [data]
            result = results[0] if isinstance(results, list) and len(results) > 0 else data
            
            stream_url = data.get("stream_url") or result.get("url") or result.get("stream_url")
            
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
