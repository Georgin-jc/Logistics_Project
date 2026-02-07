import openrouteservice as ors
import requests


def optimize_route(results, api_key, profile):
    valid_results = [
        r for r in results
        if r.get("lat") is not None and r.get("lon") is not None
    ]

    if len(valid_results) < 2:
        raise ValueError("Nicht genug gültige Adressen für eine Route.")

    depot = valid_results[0]
    depot_coord = [depot["lon"], depot["lat"]]

    jobs = []
    seen = set()
    job_id = 1

    for r in valid_results:
        # 🚫 EXCLUDE DEPOT
        if r["lat"] == depot["lat"] and r["lon"] == depot["lon"]:
            continue

        coord = (r["lon"], r["lat"])
        if coord in seen:
            continue
        seen.add(coord)

        jobs.append({
            "id": job_id,
            "location": [r["lon"], r["lat"]],
            "service": 0
        })

        r["job_id"] = job_id
        job_id += 1


    vehicles = [{
        "id": 1,
        "start": depot_coord,
        "end": depot_coord,
        "max_duration": 36000,
        "profile": profile
    }]

    payload = {
        "jobs": jobs,
        "vehicles": vehicles,
        "options": {"g": True}
    }

    print("Payload being sent to ORS:", payload)

    import json
    print("Final URL:", "https://api.openrouteservice.org/optimization")
    print("Headers:", {
        "Authorization": api_key,
        "Content-Type": "application/json"
    })
    print("Payload:", json.dumps(payload, indent=2))

    response = requests.post(
        "https://api.openrouteservice.org/optimization",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        },
        json=payload
    )
    print("Response status:", response.status_code)
    print("Response text:", response.text)


    if response.status_code != 200:
        raise ValueError(
            f"ORS API error: {response.status_code} - {response.text}"
        )

    return response.json()


def extract_order(optimized, results):
    """
    Convert ORS optimization output into an ordered list of result entries.
    """
    routes = optimized.get("routes")
    if not routes:
        raise ValueError("ORS returned no routes in optimization result.")

    steps = routes[0].get("steps", [])
    ordered = []

    for step in steps:
        if step.get("type") == "job":
            job_id = step["id"]
            for r in results:
                if r.get("job_id") == job_id:
                    ordered.append(r)
                    break

    depot = results[0]
    return [depot] + ordered + [depot]


def compute_route_stats(results, api_key,profile):
    """
    Compute total distance, duration, and segment stats.
    """
    coords = [
        [r["lon"], r["lat"]]
        for r in results
        if r.get("lat") is not None and r.get("lon") is not None
    ]

    if len(coords) < 2:
        return 0.0, 0.0, []

    client = ors.Client(key=api_key)

    route = client.directions(
        coordinates=coords,
        profile=profile,
        format="geojson"
    )

    feature = route["features"][0]
    summary = feature["properties"]["summary"]

    total_distance_km = summary["distance"] / 1000.0
    total_duration_min = summary["duration"] / 60.0

    segments = [
        {
            "distance_km": seg["distance"] / 1000.0,
            "duration_min": seg["duration"] / 60.0
        }
        for seg in feature["properties"]["segments"]
    ]

    return total_distance_km, total_duration_min, segments
