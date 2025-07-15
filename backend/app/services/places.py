import requests
from typing import List, Dict

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# can add more types here
OSM_TYPES = {
    "cafe": "amenity=cafe",
    "restaurant": "amenity=restaurant",
    "bar": "amenity=bar",
    "pub": "amenity=pub",
    "fast_food": "amenity=fast_food",
    "park": "leisure=park",
    "playground": "leisure=playground",
    "garden": "leisure=garden",
    "exhibition_center": "amenity=exhibition_centre",
    "museum": "tourism=museum",
    "art_gallery": "tourism=art_gallery",
    "theatre": "amenity=theatre",
    "cinema": "amenity=cinema",
    "library": "amenity=library",
    "attraction": "tourism=attraction",
    "zoo": "tourism=zoo",
    "aquarium": "tourism=aquarium",
    "theme_park": "tourism=theme_park",
    "shopping": "shop=mall",
    "supermarket": "shop=supermarket",
    "convenience": "shop=convenience",
    "bakery": "shop=bakery",
    "clothes": "shop=clothes",
    "shoes": "shop=shoes",
    "gift": "shop=gift",
    "sports_shop": "shop=sports",
    "hotel": "tourism=hotel",
    "hostel": "tourism=hostel",
    "motel": "tourism=motel",
    "guest_house": "tourism=guest_house",
    "camp_site": "tourism=camp_site",
    "caravan_site": "tourism=caravan_site",
    "hospital": "amenity=hospital",
    "clinic": "amenity=clinic",
    "pharmacy": "amenity=pharmacy",
    "doctors": "amenity=doctors",
    "dentist": "amenity=dentist",
    "veterinary": "amenity=veterinary",
    "school": "amenity=school",
    "university": "amenity=university",
    "college": "amenity=college",
    "kindergarten": "amenity=kindergarten",
    "bank": "amenity=bank",
    "atm": "amenity=atm",
    "post_office": "amenity=post_office",
    "police": "amenity=police",
    "fire_station": "amenity=fire_station",
    "fuel": "amenity=fuel",
    "parking": "amenity=parking",
    "charging_station": "amenity=charging_station",
    "bus_station": "amenity=bus_station",
    "taxi": "amenity=taxi",
    "train_station": "railway=station",
    "subway_entrance": "railway=subway_entrance",
    "airport": "aeroway=aerodrome",
    "ferry_terminal": "amenity=ferry_terminal",
    "marketplace": "amenity=marketplace",
    "stadium": "leisure=stadium",
    "sports_centre": "leisure=sports_centre",
    "swimming_pool": "leisure=swimming_pool",
    "fitness_centre": "leisure=fitness_centre",
    "nightclub": "amenity=nightclub",
    "casino": "amenity=casino",
    "beach": "natural=beach",
    "viewpoint": "tourism=viewpoint",
    "water_park": "leisure=water_park",
    "sauna": "amenity=sauna",
    "spa": "amenity=spa",
    "bowling_alley": "leisure=bowling_alley",
    "ice_rink": "leisure=ice_rink",
    "golf_course": "leisure=golf_course",
    "miniature_golf": "leisure=miniature_golf",
    "dog_park": "leisure=dog_park",
    "community_centre": "amenity=community_centre",
    "place_of_worship": "amenity=place_of_worship",
    "church": "amenity=place_of_worship religion=christian",
    "mosque": "amenity=place_of_worship religion=muslim",
    "synagogue": "amenity=place_of_worship religion=jewish",
    "temple": "amenity=place_of_worship religion=hindu",
    "monastery": "amenity=monastery",
    "embassy": "amenity=embassy",
    "courthouse": "amenity=courthouse",
    "townhall": "amenity=townhall",
    "public_building": "amenity=public_building",
    "memorial": "historic=memorial",
    "monument": "historic=monument",
    "ruins": "historic=ruins",
    "castle": "historic=castle",
    "fort": "historic=fort",
    "archaeological_site": "historic=archaeological_site"
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
