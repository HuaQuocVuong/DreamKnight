import pygame
import os
from knight1_animation import Animation

# ================================================================================================
# CẤU HÌNH ANIMATION CHO SLIME1
# ================================================================================================

SLIME1_ANIMATION_CONFIGS = {
    "idle": {
        "folder": "slime1_idle",
        "directions": {
            "up":    {"prefix": "slime1_idle_up",    "frames": 6},
            "down":  {"prefix": "slime1_idle_down",  "frames": 6},
            "left":  {"prefix": "slime1_idle_left",  "frames": 6},
            "right": {"prefix": "slime1_idle_right", "frames": 6},
        },
    },
    "walk": {
        "folder": "slime1_walk",
        "directions": {
            "up":    {"prefix": "slime1_walk_up",    "frames": 6},
            "down":  {"prefix": "slime1_walk_down",  "frames": 6},
            "left":  {"prefix": "slime1_walk_left",  "frames": 6},
            "right": {"prefix": "slime1_walk_right", "frames": 6},
        },
    },
    "run": {
        "folder": "slime1_run",
        "directions": {
            "up":    {"prefix": "slime1_run_up",    "frames": 8},
            "down":  {"prefix": "slime1_run_down",  "frames": 8},
            "left":  {"prefix": "slime1_run_left",  "frames": 8},
            "right": {"prefix": "slime1_run_right", "frames": 8},
        },
    },
    "attack": {
        "folder": "slime1_attack",
        "directions": {
            "up":    {"prefix": "slime1_attack_up",    "frames": 10},
            "down":  {"prefix": "slime1_attack_down",  "frames": 10},
            "left":  {"prefix": "slime1_attack_left",  "frames": 10},
            "right": {"prefix": "slime1_attack_right", "frames": 10},
        },
    },
    "hit": {
        "folder": "slime1_hurt",
        "directions": {
            "up":    {"prefix": "slime1_hurt_up",    "frames": 5},
            "down":  {"prefix": "slime1_hurt_down",  "frames": 5},
            "left":  {"prefix": "slime1_hurt_left",  "frames": 5},
            "right": {"prefix": "slime1_hurt_right", "frames": 5},
        },
    },
    "death": {
        "folder": "slime1_death",
        "directions": {
            "up":    {"prefix": "slime1_death_up",    "frames": 10},
            "down":  {"prefix": "slime1_death_down",  "frames": 10},
            "left":  {"prefix": "slime1_death_left",  "frames": 10},
            "right": {"prefix": "slime1_death_right", "frames": 10},
        },
    },
}

# Thời gian mỗi frame (ms) cho từng loại animation
FRAME_DURATIONS = {
    "idle":   200,
    "walk":   100,
    "run":    60,
    "attack": 70,
    "hit":    100,
    "death":  50,
}

# Màu fallback khi không tìm thấy sprite
FALLBACK_COLOR = (128, 0, 128)  # tím


# ================================================================================================
# CLASS LOADER — tải tất cả animation cho Slime1
# ================================================================================================

class Slime1AnimationLoader:
    """
    Tải toàn bộ animation của Slime1 từ thư mục assets.
    Trả về dict: { anim_type: { direction: Animation } }
    """

    BASE_PATH = os.path.join("assets", "resource_slime1_2_3", "slime_1")

    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        """
        Tải tất cả animation theo SLIME1_ANIMATION_CONFIGS.
        Trả về dict đầy đủ các loại animation.
        """
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Slime1Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

        all_anims = {}
        for anim_type, duration in FRAME_DURATIONS.items():
            loaded = cls._load_anim_type(anim_type, duration, scale_factor)
            all_anims[anim_type] = cls._ensure_fallback(loaded, anim_type, duration)

        return all_anims

    # ------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------

    @classmethod
    def _load_anim_type(cls, anim_type: str, frame_duration: int, scale_factor: float) -> dict:
        """Tải một loại animation (idle / walk / …) cho cả 4 hướng."""
        anims = {}
        config = SLIME1_ANIMATION_CONFIGS.get(anim_type)
        if not config:
            return anims

        folder = config["folder"]
        for direction, dir_cfg in config["directions"].items():
            frames = cls._load_frames(folder, dir_cfg, scale_factor)
            if frames:
                anims[direction] = Animation(frames, frame_duration)
                print(f"[Slime1Anim] Loaded {len(frames)} frames — {anim_type}/{direction}")

        return anims

    @classmethod
    def _load_frames(cls, folder: str, dir_cfg: dict, scale_factor: float) -> list:
        """Tải danh sách surface cho một hướng cụ thể."""
        prefix      = dir_cfg["prefix"]
        frame_count = dir_cfg["frames"]
        frames      = []

        for i in range(1, frame_count + 1):
            filepath = os.path.join(cls.BASE_PATH, folder, f"{prefix}{i}.png")
            try:
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    if scale_factor != 1.0:
                        new_size = (
                            int(img.get_width()  * scale_factor),
                            int(img.get_height() * scale_factor),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                else:
                    frames.append(cls._make_fallback())
            except Exception as e:
                print(f"[Slime1Anim] Lỗi load {filepath}: {e}")
                frames.append(cls._make_fallback())

        return frames

    @staticmethod
    def _make_fallback(size: int = 64) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill(FALLBACK_COLOR)
        return surf

    @classmethod
    def _ensure_fallback(cls, anims: dict, anim_type: str, duration: int) -> dict:
        """Đảm bảo 4 hướng đều có Animation, tạo fallback nếu thiếu."""
        if anims:
            return anims

        print(f"[Slime1Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}