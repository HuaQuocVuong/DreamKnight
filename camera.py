import pygame 

# ================================================================================================
# CLASS CAMERA — Theo dõi player và xác định vùng hiển thị trên bản đồ
# ================================================================================================

class Camera:
    def __init__(self, map_width, map_height):
        from config import VIEW_WIDTH, VIEW_HEIGHT
        
        # Vị trí góc trên trái của camera trong tọa độ bản đồ (pixel)
        self.x = 0
        self.y = 0
        
        # Kích thước toàn bộ bản đồ (dùng giới hạn camera)
        self.map_width = map_width
        self.map_height = map_height
        
        # Kích thước viewport (vùng nhìn thấy trên màn hình)
        self.view_width = VIEW_WIDTH
        self.view_height = VIEW_HEIGHT
    
    # Cập nhật vị trí camera để bám theo target (player), giới hạn trong map
    def update(self, target):
        # Tâm của target
        target_center_x = target.x + target.width // 2
        target_center_y = target.y + target.height // 2
        
        # Đặt camera sao cho target ở giữa màn hình
        self.x = target_center_x - self.view_width // 2
        self.y = target_center_y - self.view_height // 2
        
        # Giới hạn camera không ra ngoài biên bản đồ
        self.x = max(0, min(self.x, self.map_width - self.view_width))
        self.y = max(0, min(self.y, self.map_height - self.view_height))
    
    # Cập nhật kích thước viewport khi thay đổi độ phân giải
    def update_view_size(self, width, height):
        self.view_width = width
        self.view_height = height