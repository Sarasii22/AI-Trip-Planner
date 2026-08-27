import os
import json
from urllib.parse import quote_plus
from langchain_tavily import TavilySearch
from langchain_google_community import GooglePlacesTool, GooglePlacesAPIWrapper 

def maps_link(place_name: str) -> str:
    """Build a reliable Google Maps search link for any named place. Always works,
    no extra API call needed — used as a fallback when a tool doesn't return a direct URL."""
    return f"https://www.google.com/maps/search/{quote_plus(place_name)}"
class GooglePlaceSearchTool:
    def __init__(self, api_key: str):
        self.places_wrapper = GooglePlacesAPIWrapper(gplaces_api_key=api_key)
        self.places_tool = GooglePlacesTool(api_wrapper=self.places_wrapper)
    
    def google_search_attractions(self, place: str) -> dict:
        """
        Searches for attractions in the specified place using GooglePlaces API.
        """
        return self.places_tool.run(f"top attractive places in and around {place}")
    
    def google_search_restaurants(self, place: str) -> dict:
        """
        Searches for available restaurants in the specified place using GooglePlaces API.
        """
        return self.places_tool.run(f"what are the top 10 restaurants and eateries in and around {place}?")
    
    def google_search_activity(self, place: str) -> dict:
        """
        Searches for popular activities in the specified place using GooglePlaces API.
        """
        return self.places_tool.run(f"Activities in and around {place}")

    def google_search_transportation(self, place: str) -> dict:
        """
        Searches for available modes of transportation in the specified place using GooglePlaces API.
        """
        return self.places_tool.run(f"What are the different modes of transportations available in {place}")

class TavilyPlaceSearchTool:
    def __init__(self):
        pass

    def _search_with_links(self, query: str) -> str:
        """Run a Tavily search and return a markdown-friendly string that preserves
        source URLs, instead of just the synthesized answer text."""
        tavily_tool = TavilySearch(topic="general", include_answer="advanced", max_results=5)
        result = tavily_tool.invoke({"query": query})

        if not isinstance(result, dict):
            return str(result)

        parts = []
        answer = result.get("answer")
        if answer:
            parts.append(answer)

        sources = result.get("results", [])
        if sources:
            parts.append("\nSources:")
            for src in sources:
                title = src.get("title", "Link")
                url = src.get("url")
                if url:
                    parts.append(f"- [{title}]({url})")

        return "\n".join(parts) if parts else "No results found."
    
    def tavily_search_attractions(self, place: str) -> dict:
        """
        Searches for attractions in the specified place using TavilySearch.
        """
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"top attractive places in and around {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result
    
    def tavily_search_restaurants(self, place: str) -> dict:
        """
        Searches for available restaurants in the specified place using TavilySearch.
        """
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"what are the top 10 restaurants and eateries in and around {place}."})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result
    
    def tavily_search_activity(self, place: str) -> dict:
        """
        Searches for popular activities in the specified place using TavilySearch.
        """
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"activities in and around {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result

    def tavily_search_transportation(self, place: str) -> dict:
        """
        Searches for available modes of transportation in the specified place using TavilySearch.
        """
        tavily_tool = TavilySearch(topic="general", include_answer="advanced")
        result = tavily_tool.invoke({"query": f"What are the different modes of transportations available in {place}"})
        if isinstance(result, dict) and result.get("answer"):
            return result["answer"]
        return result
    