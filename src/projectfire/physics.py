import math
from dataclasses import dataclass, field

GRAVITY = 9.81  # Ускорение свободного падения (м/с^2)


@dataclass
class Projectile:
    start_x: float
    start_y: float
    velocity: float
    angle_deg: float
    x: float = field(init=False)
    y: float = field(init=False)
    time: float = 0.0
    is_flying: bool = True
    trail: list[tuple[float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.x = self.start_x
        self.y = self.start_y
        self.trail.append((self.x, self.y))

    def update(self, dt: float, ground_y: float) -> None:
        """Обновляет положение снаряда за шаг времени dt."""
        if not self.is_flying:
            return

        self.time += dt
        angle_rad = math.radians(self.angle_deg)

        vx = self.velocity * math.cos(angle_rad)
        vy = self.velocity * math.sin(angle_rad)

        self.x = self.start_x + vx * self.time
        self.y = self.start_y + vy * self.time - 0.5 * GRAVITY * (self.time ** 2)

        # Проверяем касание земли (только после начала подъёма)
        if self.y <= ground_y and self.time > 0.05:
            # Вычисляем точное время падения, чтобы снаряд лёг ровно на землю
            exact_time = (vy + math.sqrt(max(0.0, vy ** 2 + 2 * GRAVITY * (self.start_y - ground_y)))) / GRAVITY
            self.time = exact_time
            self.x = self.start_x + vx * exact_time
            self.y = ground_y
            self.is_flying = False

        self.trail.append((self.x, self.y))
