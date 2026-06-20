# slime3_animation.py
import pygame
import os
from knight1_animation import Animation

# ================================================================================================
# CẤU HÌNH ANIMATION CHO SLIME3
# ================================================================================================

SLIME3_ANIMATION_CONFIGS = {
    "idle": {
        "folder": "slime3_idle",
        "directions": {
            "up":    {"prefix": "slime3_idle_up",    "frames": 6},
            "down":  {"prefix": "slime3_idle_down",  "frames": 6},
            "left":  {"prefix": "slime3_idle_left",  "frames": 6},
            "right": {"prefix": "slime3_idle_right", "frames": 6},
        },
    },
    "walk": {
        "folder": "slime3_walk",
        "directions": {
            "up":    {"prefix": "slime3_walk_up",    "frames": 8},
            "down":  {"prefix": "slime3_walk_down",  "frames": 8},
            "left":  {"prefix": "slime3_walk_left",  "frames": 8},
            "right": {"prefix": "slime3_walk_right", "frames": 8},
        },
    },
    "run": {
        "folder": "slime3_run",
        "directions": {
            "up":    {"prefix": "slime3_run_up",    "frames": 8},
            "down":  {"prefix": "slime3_run_down",  "frames": 8},
            "left":  {"prefix": "slime3_run_left",  "frames": 8},
            "right": {"prefix": "slime3_run_right", "frames": 8},
        },
    },
    "attack": {
        "folder": "slime3_attack",
        "directions": {
            "up":    {"prefix": "slime3_attack_up",    "frames": 9},
            "down":  {"prefix": "slime3_attack_down",  "frames": 9},
            "left":  {"prefix": "slime3_attack_left",  "frames": 9},
            "right": {"prefix": "slime3_attack_right", "frames": 9},
        },
    },
    "hit": {
        "folder": "slime3_hurt",
        "directions": {
            "up":    {"prefix": "slime3_hurt_up",    "frames": 5},
            "down":  {"prefix": "slime3_hurt_down",  "frames": 5},
            "left":  {"prefix": "slime3_hurt_left",  "frames": 5},
            "right": {"prefix": "slime3_hurt_right", "frames": 5},
        },
    },
    "death": {
        "folder": "slime3_death",
        "directions": {
            "up":    {"prefix": "slime3_death_up",    "frames": 10},
            "down":  {"prefix": "slime3_death_down",  "frames": 10},
            "left":  {"prefix": "slime3_death_left",  "frames": 10},
            "right": {"prefix": "slime3_death_right", "frames": 10},
        },
    },
}

# Thời gian mỗi frame (ms) cho từng loại animation
FRAME_DURATIONS = {
    "idle":   200,
    "walk":   100,
    "run":    70,
    "attack": 60,
    "hit":    80,
    "death":  50,
}

# Màu fallback khi không tìm thấy sprite
FALLBACK_COLOR = (0, 100, 128)  # màu xanh dương đậm (để phân biệt với slime2)


# ================================================================================================
# CLASS LOADER — tải tất cả animation cho Slime3
# ================================================================================================

class Slime3AnimationLoader:
    """
    Tải toàn bộ animation của Slime3 từ thư mục assets.
    Trả về dict: { anim_type: { direction: Animation } }
    """

    BASE_PATH = os.path.join("assets", "resource_slime1_2_3", "slime_3")

    @classmethod
    def load_all(cls, scale_factor: float = 2.0) -> dict:
        """
        Tải tất cả animation theo SLIME3_ANIMATION_CONFIGS.
        Trả về dict đầy đủ các loại animation.
        """
        if not os.path.exists(cls.BASE_PATH):
            print(f"[Slime3Anim] Thư mục không tồn tại: {cls.BASE_PATH}")

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
        config = SLIME3_ANIMATION_CONFIGS.get(anim_type)
        if not config:
            return anims

        folder = config["folder"]
        for direction, dir_cfg in config["directions"].items():
            frames = cls._load_frames(folder, dir_cfg, scale_factor)
            if frames:
                anims[direction] = Animation(frames, frame_duration)
                print(f"[Slime3Anim] Loaded {len(frames)} frames — {anim_type}/{direction}")

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
                print(f"[Slime3Anim] Lỗi load {filepath}: {e}")
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

        print(f"[Slime3Anim] Tạo animation fallback cho: {anim_type}")
        fallback_frame = [cls._make_fallback()]
        return {d: Animation(fallback_frame, duration) for d in ("up", "down", "left", "right")}