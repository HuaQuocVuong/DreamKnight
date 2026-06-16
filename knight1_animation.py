import pygame
import os
from config import PLAYER_SPEED, RUN_SPEED

#================================================================================================
# Lớp Animation quản lý chuỗi các frame
# Lớp Animation: quản lý một chuỗi các frame ảnh để tạo hiệu ứng chuyển động.
# Tự động cập nhật frame theo thời gian dựa trên frame_duration (ms)
# Hỗ trợ reset về frame đầu tiên.
#================================================================================================

class Animation:
    def __init__(self, frames, frame_duration=90):
        self.frames = frames    # Danh sách các frame ảnh
        self.frame_count = len(frames)  # Tổng số frame
        self.frame_duration = frame_duration   # Thời gian mỗi frame (ms)
        self.current_frame_index = 0    # Chỉ số frame hiện tại
        self.last_update_time = 0   # Thời điểm cập nhật frame gần nhất (ms)
        self.current_frame = frames[0] if frames else None  # Frame đang hiển thị
        self.is_finished = False  # Đánh dấu animation đã kết thúc (cho animation không loop)
        self.loop = True  # Có lặp lại không
        
    def update(self):
        """Cập nhật animation, chuyển sang frame tiếp theo nếu đủ thời gian"""
        if not self.frames or self.is_finished:
            return
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_update_time > self.frame_duration:
            self.current_frame_index += 1
            
            # Kiểm tra nếu đã hết frame
            if self.current_frame_index >= self.frame_count:
                if self.loop:
                    self.current_frame_index = 0  # Quay lại frame đầu
                else:
                    self.current_frame_index = self.frame_count - 1  # Giữ frame cuối
                    self.is_finished = True  # Đánh dấu đã kết thúc
            
            self.current_frame = self.frames[self.current_frame_index]
            self.last_update_time = current_time
    
    def reset(self):
        """Reset animation về frame đầu tiên"""
        self.current_frame_index = 0
        self.current_frame = self.frames[0] if self.frames else None
        self.last_update_time = 0
        self.is_finished = False
    
    def set_loop(self, loop):
        """Đặt chế độ loop cho animation"""
        self.loop = loop
        if loop:
            self.is_finished = False

# ============================================================
# ĐỊNH NGHĨA CẤU HÌNH CHO TỪNG LOẠI ANIMATION
# ============================================================

ANIMATION_CONFIGS = {
    # 1. IDLE - Đứng yên
    "idle": {
        "folder": "knight_lv3_idle",
        "directions": {
            "up": {"prefix": "knight_lv3_idle_up", "frames": 4},
            "down": {"prefix": "knight_lv3_idle_down", "frames": 12},
            "left": {"prefix": "knight_lv3_idle_left", "frames": 12},
            "right": {"prefix": "knight_lv3_idle_right", "frames": 12}
        },
        "default_frame_duration": 150
    },
    
    # 2. WALK - Đi bộ
    "walk": {
        "folder": "knight_lv3_walk",
        "directions": {
            "up": {"prefix": "knight_lv3_walk_up", "frames": 6},
            "down": {"prefix": "knight_lv3_walk_down", "frames": 6},
            "left": {"prefix": "knight_lv3_walk_left", "frames": 6},
            "right": {"prefix": "knight_lv3_walk_right", "frames": 6}
        },
        "default_frame_duration": 100
    },
    
    # 3. RUN - Chạy nhanh
    "run": {
        "folder": "knight_lv3_run",
        "directions": {
            "up": {"prefix": "knight_lv3_run_up", "frames": 8},
            "down": {"prefix": "knight_lv3_run_down", "frames": 8},
            "left": {"prefix": "knight_lv3_run_left", "frames": 8},
            "right": {"prefix": "knight_lv3_run_right", "frames": 8}
        },
        "default_frame_duration": 70
    },
    
    # 4. ATTACK IDLE - Tấn công khi đứng yên
    "attack_idle": {
        "folder": "knight_lv3_idle_attack",
        "directions": {
            "up": {"prefix": "knight_lv3_idle_attack_up", "frames": 8},
            "down": {"prefix": "knight_lv3_idle_attack_down", "frames": 8},
            "left": {"prefix": "knight_lv3_idle_attack_left", "frames": 8},
            "right": {"prefix": "knight_lv3_idle_attack_right", "frames": 8}
        },
        "default_frame_duration": 50
    },
    
    # 5. ATTACK WALK - Tấn công khi đi bộ
    "attack_walk": {
        "folder": "knight_lv3_walk_attack",
        "directions": {
            "up": {"prefix": "knight_lv3_walk_attack_up", "frames": 8},
            "down": {"prefix": "knight_lv3_walk_attack_down", "frames": 8},
            "left": {"prefix": "knight_lv3_walk_attack_left", "frames": 8},
            "right": {"prefix": "knight_lv3_walk_attack_right", "frames": 8}
        },
        "default_frame_duration": 50
    },
    
    # 6. ATTACK RUN - Tấn công khi chạy
    "attack_run": {
        "folder": "knight_lv3_run_attack",
        "directions": {
            "up": {"prefix": "knight_lv3_run_attack_up", "frames": 8},
            "down": {"prefix": "knight_lv3_run_attack_down", "frames": 8},
            "left": {"prefix": "knight_lv3_run_attack_left", "frames": 8},
            "right": {"prefix": "knight_lv3_run_attack_right", "frames": 8}
        },
        "default_frame_duration": 40
    },
    
    # 7. DASH - Lướt nhanh
    "dash": {
        "folder": "knight_lv3_dash01",
        "directions": {
            "up": {"prefix": "knight_lv3_dash_up", "frames": 5},
            "down": {"prefix": "knight_lv3_dash_down", "frames": 5},
            "left": {"prefix": "knight_lv3_dash_left", "frames": 5},
            "right": {"prefix": "knight_lv3_dash_right", "frames": 5}
        },
        "default_frame_duration": 40
    },
    
    # 8. HIT - Dính đòn (THÊM MỚI)
    "hit": {
        "folder": "knight_lv3_hurt",  # Bạn cần tạo thư mục này và thêm ảnh
        "directions": {
            "up": {"prefix": "knight_lv3_hurt_up", "frames": 5},
            "down": {"prefix": "knight_lv3_hurt_down", "frames": 5},
            "left": {"prefix": "knight_lv3_hurt_left", "frames": 5},
            "right": {"prefix": "knight_lv3_hurt_right", "frames": 5}
        },
        "default_frame_duration": 80
    }
}

# ============================================================
# LỚP QUẢN LÝ ANIMATION
# ============================================================

class AnimationManager:
    """Quản lý tất cả animations của player"""
    
    def __init__(self, scale_factor=2.0):
        self.scale_factor = scale_factor
        self.animations_cache = {}  # Cache để tránh load lại ảnh nhiều lần
        
    def _load_and_scale_image(self, filepath):
        """
        Load và scale ảnh theo scale_factor
        
        Args:
            filepath: Đường dẫn đến file ảnh
            
        Returns:
            pygame.Surface: Ảnh đã được scale
        """
        try:
            img = pygame.image.load(filepath).convert_alpha()
            original_size = img.get_size()
            new_size = (int(original_size[0] * self.scale_factor), 
                       int(original_size[1] * self.scale_factor))
            return pygame.transform.scale(img, new_size)
        except Exception as e:
            print(f"Error loading image {filepath}: {e}")
            # Trả về surface trắng nếu không load được
            return pygame.Surface((32, 32), pygame.SRCALPHA)
    
    def load_animation(self, animation_type, direction):
        """
        Load animation dựa trên type và direction
        
        Args:
            animation_type: Loại animation ("idle", "walk", "run", "attack_idle", 
                           "attack_walk", "attack_run", "dash", "hit")
            direction: Hướng ("up", "down", "left", "right")
            
        Returns:
            list: Danh sách các frame ảnh đã load
        """
        cache_key = f"{animation_type}_{direction}"
        
        # Kiểm tra cache trước
        if cache_key in self.animations_cache:
            return self.animations_cache[cache_key]
        
        # Lấy config từ ANIMATION_CONFIGS
        config = ANIMATION_CONFIGS.get(animation_type)
        if not config:
            raise ValueError(f"Unknown animation type: {animation_type}")
        
        direction_config = config["directions"].get(direction)
        if not direction_config:
            raise ValueError(f"Unknown direction: {direction} for animation type: {animation_type}")
        
        # Load frames
        frames = []
        folder = config["folder"]
        prefix = direction_config["prefix"]
        frame_count = direction_config["frames"]
        
        for i in range(1, frame_count + 1):
            filename = f"{prefix}{i}.png"
            filepath = os.path.join("assets", "knight_lv3", folder, filename)
            scaled_img = self._load_and_scale_image(filepath)
            frames.append(scaled_img)
        
        # Cache kết quả
        self.animations_cache[cache_key] = frames
        return frames
    
    def create_animation(self, animation_type, direction, frame_duration=None):
        """
        Tạo đối tượng Animation từ type và direction
        
        Args:
            animation_type: Loại animation
            direction: Hướng
            frame_duration: Thời gian mỗi frame (ms), nếu None sẽ dùng default
            
        Returns:
            Animation: Đối tượng Animation
        """
        if frame_duration is None:
            config = ANIMATION_CONFIGS.get(animation_type, {})
            frame_duration = config.get("default_frame_duration", 90)
        
        frames = self.load_animation(animation_type, direction)
        
        # Kiểm tra xem animation có cần loop không
        loop = True
        if animation_type == "hit":
            loop = True  # Hit animation lặp lại trong thời gian hit
        
        anim = Animation(frames, frame_duration)
        anim.loop = loop
        return anim

# ============================================================
# CÁC HÀM LOAD FRAMES (GIỮ NGUYÊN ĐỂ TƯƠNG THÍCH)
# ============================================================

# Tạo một instance AnimationManager duy nhất để tái sử dụng
_animation_manager = AnimationManager(scale_factor=2.0)

def load_idle_frames(direction):
    """Load frames đứng yên"""
    return _animation_manager.load_animation("idle", direction)

def load_walk_frames(direction):
    """Load frames đi bộ"""
    return _animation_manager.load_animation("walk", direction)

def load_run_frames(direction):
    """Load frames chạy nhanh"""
    return _animation_manager.load_animation("run", direction)

def load_attack_idle_frames(direction):
    """Load frames tấn công khi đứng yên"""
    return _animation_manager.load_animation("attack_idle", direction)

def load_attack_walk_frames(direction):
    """Load frames tấn công khi đi bộ"""
    return _animation_manager.load_animation("attack_walk", direction)

def load_attack_run_frames(direction):
    """Load frames tấn công khi chạy"""
    return _animation_manager.load_animation("attack_run", direction)

def load_dash_frames(direction):
    """Load frames dash (lướt)"""
    return _animation_manager.load_animation("dash", direction)

def load_hit_frames(direction):
    """Load frames hit (dính đòn) - THÊM MỚI"""
    return _animation_manager.load_animation("hit", direction)