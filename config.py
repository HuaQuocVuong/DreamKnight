# ==================== CẤU HÌNH GAME ====================

# Kích thước cửa sổ hiển thị chính của game (tính bằng pixel)

#SCREEN_WIDTH = 1220  #1920  # Độ rộng cửa sổ game 800
#SCREEN_HEIGHT = 540  #1040  # Độ cao cửa sổ game 520

#SCREEN_WIDTH = 1280 # Độ rộng cửa sổ game -100 cho đến khi phù hợp
#SCREEN_HEIGHT  = 720 # Độ cao cửa sổ game -100 cho đến khi phù hợp

#Không xóa!!!!!!!
SCREEN_WIDTH = 1920 # Độ rộng cửa sổ game -100 cho đến khi phù hợp
SCREEN_HEIGHT  = 1040 # Độ cao cửa sổ game -100 cho đến khi phù hợp


# Kích thước vùng nhìn của camera (vùng thế giới game được hiển thị trong game_surface)
VIEW_WIDTH = 760    # Độ rộng vùng nhìn (camera viewport width) 600
VIEW_HEIGHT = 370   # Độ cao vùng nhìn (camera viewport height)  400

#Thiết lập mặc định
VIEW_WIDTH =  800   # Độ rộng vùng nhìn (camera viewport width) 600
VIEW_HEIGHT = 450  # Độ cao vùng nhìn (camera viewport height)  400

# Kích thước toàn bộ bản đồ game (thế giới game rộng hơn màn hình)
MAP_WIDTH = 1920   # Chiều rộng map (pixel)
MAP_HEIGHT = 1080  # Chiều cao map (pixel)

# Kích thước khung giới hạn (hitbox) của nhân vật chính
PLAYER_WIDTH = 40   # Chiều rộng nhân vật (dùng cho va chạm)
PLAYER_HEIGHT = 40  # Chiều cao nhân vật

# Giới hạn FPS (frames per second) - thiết lập rất cao (10000) có thể để test hoặc debug
FPS = 1000000000000

# Tốc độ di chuyển cơ bản của nhân vật (pixel/frame)
PLAYER_SPEED = 3.0

# Tốc độ khi chạy (bằng nửa PLAYER_SPEED? thực tế là 6 > 3 nên nhanh gấp đôi)
RUN_SPEED = 5.0 # Tốc độ chạy (nhanh hơn đi bộ)

# ==================== ĐƯỜNG DẪN ẢNH ====================

# Đường dẫn đến file ảnh bản đồ nền (map background)
MAP_IMAGE_PATH = "assets/map/MAP002.png"

# Chế độ debug: in ra thông tin, hiển thị hitbox, v.v.
DEBUG_MODE = False 
#DEBUG_MODE = True 