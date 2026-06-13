from .osrm import geocode_location, get_osrm_route

MAX_DRIVE_HOURS = 11.0
MAX_SHIFT_HOURS = 14.0
REST_BREAK_THRESHOLD = 8.0
MANDATORY_REST_HOURS = 10.0
CYCLE_LIMIT_HOURS = 70.0
PICKUP_DROPOFF_HOURS = 1.0

def plan_hos_trip(current_loc, pickup_loc, dropoff_loc, cycle_used=0.0):
    start_lat, start_lon, start_name = geocode_location(current_loc)
    p_lat, p_lon, p_name = geocode_location(pickup_loc)
    d_lat, d_lon, d_name = geocode_location(dropoff_loc)

    dist_miles, drive_hrs, route_geometry = get_osrm_route(
        (start_lat, start_lon), (p_lat, p_lon), (d_lat, d_lon)
    )

    timeline = []
    stops = []

    def add_event(status, duration, location, remark):
        timeline.append({
            'status': status,
            'duration': round(duration, 2),
            'location': location,
            'remark': remark
        })

    total_trip_duration = 0.0
    accumulated_cycle_hours = float(cycle_used)
    shift_hours = 0.0
    shift_drive_hours = 0.0
    drive_since_break = 0.0
    day_clock = 0.0
    remaining_drive = drive_hrs

    add_event(4, 0.25, start_name.split(',')[0], 'Pre-Trip Inspection')
    shift_hours += 0.25
    day_clock += 0.25
    total_trip_duration += 0.25
    accumulated_cycle_hours += 0.25

    add_event(4, PICKUP_DROPOFF_HOURS, p_name.split(',')[0], 'Loading / Pickup Freight')
    shift_hours += PICKUP_DROPOFF_HOURS
    day_clock += PICKUP_DROPOFF_HOURS
    total_trip_duration += PICKUP_DROPOFF_HOURS
    accumulated_cycle_hours += PICKUP_DROPOFF_HOURS

    stops.append({
        'lat': p_lat, 'lng': p_lon,
        'label': f"Pickup: {p_name.split(',')[0]}",
        'type': 'Pickup', 'duration_hours': PICKUP_DROPOFF_HOURS
    })

    while remaining_drive > 0.001:
        if shift_drive_hours >= MAX_DRIVE_HOURS or shift_hours >= MAX_SHIFT_HOURS:
            time_left_in_day = 24.0 - (day_clock % 24.0)
            rest_duration = MANDATORY_REST_HOURS if (time_left_in_day < 0.01 or time_left_in_day == 24.0) else max(MANDATORY_REST_HOURS, time_left_in_day)
            add_event(2, rest_duration, 'Rest Area / Truck Stop', '10-Hour Mandatory Shift Reset')
            total_trip_duration += rest_duration
            day_clock += rest_duration
            shift_hours = 0.0
            shift_drive_hours = 0.0
            drive_since_break = 0.0
            continue

        if drive_since_break >= REST_BREAK_THRESHOLD:
            add_event(1, 0.5, 'Rest Stop', '30-Minute Required Rest Break')
            shift_hours += 0.5
            day_clock += 0.5
            drive_since_break = 0.0
            total_trip_duration += 0.5
            continue

        chunk = min(remaining_drive, MAX_DRIVE_HOURS - shift_drive_hours, MAX_SHIFT_HOURS - shift_hours, REST_BREAK_THRESHOLD - drive_since_break)
        if chunk > 0.001:
            add_event(3, chunk, 'Interstate Drive', 'Driving')
            remaining_drive -= chunk
            shift_drive_hours += chunk
            drive_since_break += chunk
            shift_hours += chunk
            day_clock += chunk
            total_trip_duration += chunk
            accumulated_cycle_hours += chunk

    add_event(4, PICKUP_DROPOFF_HOURS, d_name.split(',')[0], 'Unloading / Dropoff Freight')
    add_event(4, 0.25, d_name.split(',')[0], 'Post-Trip Inspection')
    total_trip_duration += (PICKUP_DROPOFF_HOURS + 0.25)
    day_clock += (PICKUP_DROPOFF_HOURS + 0.25)
    accumulated_cycle_hours += (PICKUP_DROPOFF_HOURS + 0.25)

    stops.append({
        'lat': d_lat, 'lng': d_lon,
        'label': f"Dropoff: {d_name.split(',')[0]}",
        'type': 'Dropoff', 'duration_hours': PICKUP_DROPOFF_HOURS
    })

    return {
        'total_distance_miles': round(dist_miles, 1),
        'total_drive_hours': round(drive_hrs, 2),
        'total_trip_duration_hours': round(total_trip_duration, 2),
        'accumulated_cycle_hours': round(accumulated_cycle_hours, 2),
        'cycle_violation': accumulated_cycle_hours > CYCLE_LIMIT_HOURS,
        'route_geometry': route_geometry,
        'stops': stops,
        'timeline': timeline
    }
