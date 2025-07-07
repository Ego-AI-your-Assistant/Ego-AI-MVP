import requests
from typing import List, Dict

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# can add more types here
OSM_TYPES = {
    "cafe": "amenity=cafe",
    "park": "leisure=park",
    "library": "amenity=library",
    "restaurant": "amenity=restaurant",
    "bar": "amenity=bar",
    "supermarket": "shop=supermarket"
}

def nearby_places(lat: str, lon: str, place_type: str) -> List[Dict]:
    """
    Returns a list of nearby places of the given type using Overpass API.
    Returns JSON:
    [
        {
            "name": "Coffee House",
            "type": "cafe",
            "lat": "55.751244",
            "lon": "37.618423",
            "address": "Tverskaya St, 1, Moscow"
        },
        ...
    ]
    """
    if place_type not in OSM_TYPES:
        raise ValueError(f"Unsupported place type: {place_type}")
    tag = OSM_TYPES[place_type]
    # Поиск в радиусе 1000м
    query = f"""
    [out:json][timeout:25];
    node[{tag}](around:1000,{lat},{lon});
    out body;
    """.format(tag=tag, lat=lat, lon=lon)
    response = requests.post(OVERPASS_URL, data={"data": query})
    response.raise_for_status()
    data = response.json()
    results = []
    for el in data.get("elements", []):
        results.append({
            "name": el.get("tags", {}).get("name", ""),
            "type": place_type,
            "lat": str(el.get("lat")),
            "lon": str(el.get("lon")),
            "address": el.get("tags", {}).get("addr:full") or el.get("tags", {}).get("addr:street", "")
        })
    return results 
