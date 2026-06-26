import pygame
import os
from config import PLAYER_SPEED, RUN_SPEED

# ================================================================================================
# CLASS ANIMATION — Quản lý chuỗi frame, tự động chuyển frame theo thời gian
# ================================================================================================

class Animation:
    def __init__(self, frames, frame_duration=90):
        """
        frames: danh sách Surface
        frame_duration: thời gian mỗi frame (ms), mặc định 90ms
        """
        self.frames = frames
        self.frame_count = len(frames)
        self.frame_duration = frame_duration
        self.current_frame_index = 0
        self.last_update_time = 0
        self.current_frame = frames[0] if frames else None
        self.is_finished = False  # Cờ animation đã kết thúc (cho anim không loop)
        self.loop = True          # Có lặp lại không
        
    # Chuyển frame tiếp theo nếu đủ thời gian, loop về đầu nếu hết
    def update(self):
        if not self.frames or self.is_finished:
            return
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_update_time > self.frame_duration:
            self.current_frame_index += 1
            
            if self.current_frame_index >= self.frame_count:
                if self.loop:
                    self.current_frame_index = 0  # Loop về frame đầu
                else:
                    self.current_frame_index = self.frame_count - 1  # Giữ frame cuối
                    self.is_finished = True
            
            self.current_frame = self.frames[self.current_frame_index]
            self.last_update_time = current_time
    
    # Reset về frame đầu tiên
    def reset(self):
        self.current_frame_index = 0
        self.current_frame = self.frames[0] if self.frames else None
        self.last_update_time = 0
        self.is_finished = False
    
    # Bật/tắt chế độ loop
    def set_loop(self, loop):
        self.loop = loop
        if loop:
            self.is_finished = False


# ================================================================================================
# CẤU HÌNH ANIMATION — Định nghĩa folder, prefix, số frame cho từng loại
# ================================================================================================

ANIMATION_CONFIGS = {
    # Idle: đứng yên (150ms/frame mặc định)
    "idle": {
        "folder": "knight_lv3_idle",
        "directions": {
            "up":    {"prefix": "knight_lv3_idle_up",    "frames": 4},
            "down":  {"prefix": "knight_lv3_idle_down",  "frames": 12},
            "left":  {"prefix": "knight_lv3_idle_left",  "frames": 12},
            "right": {"prefix": "knight_lv3_idle_right", "frames": 12}
        },
        "default_frame_duration": 150
    },
    
    # Walk: đi bộ (100ms/frame)
    "walk": {
        "folder": "knight_lv3_walk",
        "directions": {
            "up":    {"prefix": "knight_lv3_walk_up",    "frames": 6},
            "down":  {"prefix": "knight_lv3_walk_down",  "frames": 6},
            "left":  {"prefix": "knight_lv3_walk_left",  "frames": 6},
            "right": {"prefix": "knight_lv3_walk_right", "frames": 6}
        },
        "default_frame_duration": 100
    },
    
    # Run: chạy nhanh (70ms/frame)
    "run": {
        "folder": "knight_lv3_run",
        "directions": {
            "up":    {"prefix": "knight_lv3_run_up",    "frames": 8},
            "down":  {"prefix": "knight_lv3_run_down",  "frames": 8},
            "left":  {"prefix": "knight_lv3_run_left",  "frames": 8},
            "right": {"prefix": "knight_lv3_run_right", "frames": 8}
        },
        "default_frame_duration": 70
    },
    
    # Attack idle: tấn công khi đứng yên (50ms/frame)
    "attack_idle": {
        "folder": "knight_lv3_idle_attack",
        "directions": {
            "up":    {"prefix": "knight_lv3_idle_attack_up",    "frames": 8},
            "down":  {"prefix": "knight_lv3_idle_attack_down",  "frames": 8},
            "left":  {"prefix": "knight_lv3_idle_attack_left",  "frames": 8},
            "right": {"prefix": "knight_lv3_idle_attack_right", "frames": 8}
        },
        "default_frame_duration": 50
    },
    
    # Attack walk: tấn công khi đi bộ (50ms/frame)
    "attack_walk": {
        "folder": "knight_lv3_walk_attack",
        "directions": {
            "up":    {"prefix": "knight_lv3_walk_attack_up",    "frames": 8},
            "down":  {"prefix": "knight_lv3_walk_attack_down",  "frames": 8},
            "left":  {"prefix": "knight_lv3_walk_attack_left",  "frames": 8},
            "right": {"prefix": "knight_lv3_walk_attack_right", "frames": 8}
        },
        "default_frame_duration": 50
    },
    
    # Attack run: tấn công khi chạy (40ms/frame — nhanh nhất)
    "attack_run": {
        "folder": "knight_lv3_run_attack",
        "directions": {
            "up":    {"prefix": "knight_lv3_run_attack_up",    "frames": 8},
            "down":  {"prefix": "knight_lv3_run_attack_down",  "frames": 8},
            "left":  {"prefix": "knight_lv3_run_attack_left",  "frames": 8},
            "right": {"prefix": "knight_lv3_run_attack_right", "frames": 8}
        },
        "default_frame_duration": 40
    },
    
    # Dash: lướt nhanh (40ms/frame)
    "dash": {
        "folder": "knight_lv3_dash01",
        "directions": {
            "up":    {"prefix": "knight_lv3_dash_up",    "frames": 5},
            "down":  {"prefix": "knight_lv3_dash_down",  "frames": 5},
            "left":  {"prefix": "knight_lv3_dash_left",  "frames": 5},
            "right": {"prefix": "knight_lv3_dash_right", "frames": 5}
        },
        "default_frame_duration": 40
    },
    
    # Hit: dính đòn (80ms/frame)
    "hit": {
        "folder": "knight_lv3_hurt",
        "directions": {
            "up":    {"prefix": "knight_lv3_hurt_up",    "frames": 5},
            "down":  {"prefix": "knight_lv3_hurt_down",  "frames": 5},
            "left":  {"prefix": "knight_lv3_hurt_left",  "frames": 5},
            "right": {"prefix": "knight_lv3_hurt_right", "frames": 5}
        },
        "default_frame_duration": 80
    }
}


# ================================================================================================
# CLASS ANIMATIONMANAGER — Load và cache animation, tạo đối tượng Animation
# ================================================================================================

class AnimationManager:
    def __init__(self, scale_factor=2.0):
        self.scale_factor = scale_factor
        self.animations_cache = {}  # Cache frame đã load để tránh load lại
        
    # Load và scale 1 ảnh, trả về Surface trắng nếu lỗi
    def _load_and_scale_image(self, filepath):
        try:
            img = pygame.image.load(filepath).convert_alpha()
            original_size = img.get_size()
            new_size = (int(original_size[0] * self.scale_factor), 
                       int(original_size[1] * self.scale_factor))
            return pygame.transform.scale(img, new_size)
        except Exception as e:
            print(f"Error loading image {filepath}: {e}")
            return pygame.Surface((32, 32), pygame.SRCALPHA)
    
    # Load danh sách frame cho animation_type + direction (có cache)
    def load_animation(self, animation_type, direction):
        cache_key = f"{animation_type}_{direction}"
        
        if cache_key in self.animations_cache:
            return self.animations_cache[cache_key]
        
        config = ANIMATION_CONFIGS.get(animation_type)
        if not config:
            raise ValueError(f"Unknown animation type: {animation_type}")
        
        direction_config = config["directions"].get(direction)
        if not direction_config:
            raise ValueError(f"Unknown direction: {direction} for animation type: {animation_type}")
        
        frames = []
        folder = config["folder"]
        prefix = direction_config["prefix"]
        frame_count = direction_config["frames"]
        
        # Load từng frame: {prefix}1.png → {prefix}{frame_count}.png
        for i in range(1, frame_count + 1):
            filename = f"{prefix}{i}.png"
            filepath = os.path.join("assets", "knight_lv3", folder, filename)
            scaled_img = self._load_and_scale_image(filepath)
            frames.append(scaled_img)
        
        self.animations_cache[cache_key] = frames
        return frames
    
    # Tạo đối tượng Animation từ type + direction
    def create_animation(self, animation_type, direction, frame_duration=None):
        if frame_duration is None:
            config = ANIMATION_CONFIGS.get(animation_type, {})
            frame_duration = config.get("default_frame_duration", 90)
        
        frames = self.load_animation(animation_type, direction)
        
        # Hit animation luôn loop
        loop = True
        if animation_type == "hit":
            loop = True
        
        anim = Animation(frames, frame_duration)
        anim.loop = loop
        return anim


# ================================================================================================
# HÀM LOAD FRAMES — Giữ nguyên để tương thích với code cũ
# ================================================================================================

# Instance duy nhất, scale x2
_animation_manager = AnimationManager(scale_factor=2.0)

def load_idle_frames(direction):
    return _animation_manager.load_animation("idle", direction)

def load_walk_frames(direction):
    return _animation_manager.load_animation("walk", direction)

def load_run_frames(direction):
    return _animation_manager.load_animation("run", direction)

def load_attack_idle_frames(direction):
    return _animation_manager.load_animation("attack_idle", direction)

def load_attack_walk_frames(direction):
    return _animation_manager.load_animation("attack_walk", direction)

def load_attack_run_frames(direction):
    return _animation_manager.load_animation("attack_run", direction)

def load_dash_frames(direction):
    return _animation_manager.load_animation("dash", direction)

def load_hit_frames(direction):
    return _animation_manager.load_animation("hit", direction)