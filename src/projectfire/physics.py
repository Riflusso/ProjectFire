import math

GRAVITY = 9.81


def step_projectile(
    start_x: float,
    start_y: float,
    velocity: float,
    angle_deg: float,
    flight_time: float,
    dt: float,
    ground_y: float,
    trail: list[tuple[float, float]],
) -> tuple[float, float, float, bool]:
    flight_time += dt
    angle_rad = math.radians(angle_deg)

    vx = velocity * math.cos(angle_rad)
    vy = velocity * math.sin(angle_rad)

    x = start_x + vx * flight_time
    y = start_y + vy * flight_time - 0.5 * GRAVITY * (flight_time ** 2)
    is_flying = True

    if y <= ground_y and flight_time > 0.05:
        discriminant = max(0.0, vy ** 2 + 2.0 * GRAVITY * (start_y - ground_y))
        exact_time = (vy + math.sqrt(discriminant)) / GRAVITY
        flight_time = exact_time
        x = start_x + vx * exact_time
        y = ground_y
        is_flying = False

    trail.append((x, y))
    return x, y, flight_time, is_flying
