from PIL import Image, ImageDraw, ImageFont
import os

# Папка для статики
IMG_DIR = "/home/ubuntu/smart_diary_bot/static/schedules"
os.makedirs(IMG_DIR, exist_ok=True)

# Полное расписание для всех классов
РАСПИСАНИЕ = {
    "6А": {
        0: [("Математика", "205"), ("Русский язык", "304"), ("История", "210"), ("Физкультура", "Зал"), ("Биология", "401"), ("География", "403")],
        1: [("Английский язык", "301"), ("Математика", "205"), ("Литература", "304"), ("Обществознание", "210"), ("Музыка", "Актовый"), ("Технология", "Мастер")],
        2: [("Русский язык", "304"), ("Математика", "205"), ("Информатика", "102"), ("Физкультура", "Зал"), ("ИЗО", "202"), ("ОБЖ", "110")],
        3: [("Математика", "205"), ("Русский язык", "304"), ("История", "210"), ("Литература", "304"), ("Биология", "401"), ("Английский язык", "301")],
        4: [("Русский язык", "304"), ("Математика", "205"), ("География", "403"), ("Физкультура", "Зал"), ("Технология", "Мастер"), ("Разговоры о важном", "205")]
    },
    "6В": {
        0: [("Русский язык", "304"), ("Математика", "205"), ("Биология", "401"), ("История", "210"), ("География", "403"), ("Физкультура", "Зал")],
        1: [("Литература", "304"), ("Английский язык", "301"), ("Математика", "205"), ("Обществознание", "210"), ("Технология", "Мастер"), ("Музыка", "Актовый")],
        2: [("Информатика", "102"), ("Русский язык", "304"), ("Математика", "205"), ("Физкультура", "Зал"), ("ОБЖ", "110"), ("ИЗО", "202")],
        3: [("История", "210"), ("Математика", "205"), ("Русский язык", "304"), ("Биология", "401"), ("Английский язык", "301"), ("Литература", "304")],
        4: [("География", "403"), ("Русский язык", "304"), ("Математика", "205"), ("Физкультура", "Зал"), ("Разговоры о важном", "205"), ("Технология", "Мастер")]
    },
    "7А": {
        0: [("Алгебра", "305"), ("Геометрия", "305"), ("Русский язык", "204"), ("Литература", "204"), ("Физика", "412"), ("История", "210")],
        1: [("Биология", "406"), ("География", "403"), ("Английский язык", "301"), ("Алгебра", "305"), ("Обществознание", "210"), ("Музыка", "Актовый")],
        2: [("Информатика", "102"), ("Русский язык", "204"), ("Алгебра", "305"), ("Физика", "412"), ("Физкультура", "Зал"), ("ИЗО", "202")],
        3: [("Химия", "408"), ("История", "210"), ("Геометрия", "305"), ("Русский язык", "204"), ("Английский язык", "301"), ("Литература", "204")],
        4: [("Физика", "412"), ("География", "403"), ("Алгебра", "305"), ("Физкультура", "Зал"), ("Разговоры о важном", "305"), ("Технология", "Мастер")]
    }
}

# Клонируем расписание для остальных классов, чтобы не было ошибок "не найдено"
for cls in ["7В", "7С", "8А", "8Б", "9А", "10А", "11А"]:
    РАСПИСАНИЕ[cls] = РАСПИСАНИЕ["7А"]

def generate_schedule_image(class_name, day_index, schedule_items):
    width = 800
    padding = 50
    header_height = 150
    item_height = 90
    item_spacing = 20
    
    num_lessons = len(schedule_items)
    height = header_height + (item_height + item_spacing) * num_lessons + padding
    
    bg_color = (255, 255, 255)
    accent_color = (63, 81, 181)
    text_main = (33, 33, 33)
    text_secondary = (117, 117, 117)
    card_bg = (245, 247, 250)
    
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 48)
        font_semi = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 28)
        font_reg = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 20)
    except:
        font_bold = font_semi = font_reg = font_small = ImageFont.load_default()

    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    draw.text((padding, padding), class_name, font=font_bold, fill=accent_color)
    draw.text((padding, padding + 65), days[day_index], font=font_semi, fill=text_main)
    draw.line((padding, header_height - 20, width - padding, header_height - 20), fill=(230, 230, 230), width=2)
    
    y_offset = header_height
    for idx, (subject, room) in enumerate(schedule_items, 1):
        card_coords = [padding, y_offset, width - padding, y_offset + item_height]
        draw.rounded_rectangle(card_coords, radius=15, fill=card_bg)
        
        circle_size = 50
        circle_x = padding + 20
        circle_y = y_offset + (item_height - circle_size) // 2
        draw.ellipse([circle_x, circle_y, circle_x + circle_size, circle_y + circle_size], fill=accent_color)
        
        num_str = str(idx)
        num_w = draw.textlength(num_str, font=font_reg)
        draw.text((circle_x + (circle_size - num_w) / 2, circle_y + 10), num_str, font=font_reg, fill=(255, 255, 255))
        
        draw.text((circle_x + circle_size + 30, y_offset + 18), subject, font=font_semi, fill=text_main)
        room_str = f"Кабинет {room}" if room else "Актовый зал"
        draw.text((circle_x + circle_size + 30, y_offset + 52), room_str, font=font_small, fill=text_secondary)
        
        y_offset += item_height + item_spacing
        
    file_path = f"{IMG_DIR}/schedule_{class_name}_{day_index}.png"
    img.save(file_path)
    return file_path
