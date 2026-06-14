import requests

def geocode_location(address):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
    headers = {'User-Agent': 'HOS-Planner-App/1.0'}
    response = requests.get(url, headers=headers, timeout=10)
    res = response.json()
    if res:
        return float(res[0]['lat']), float(res[0]['lon']), res[0]['display_name']
    raise ValueError(f"Could not locate address: {address}")

def get_osrm_route(start_coords, pickup_coords, dropoff_coords):
    coords_str = f"{start_coords[1]},{start_coords[0]};{pickup_coords[1]},{pickup_coords[0]};{dropoff_coords[1]},{dropoff_coords[0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    response = requests.get(url, timeout=10)
    res = response.json()
    if res.get('code') != 'Ok':
        raise Exception("Failed to calculate route via OSRM.")
    route = res['routes'][0]
    return route['distance'] * 0.000621371, route['duration'] / 3600.0, route['geometry']
