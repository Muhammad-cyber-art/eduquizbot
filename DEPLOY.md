# 🚀 Linux VPS Deployment Guide (Enterprise Grade)

Ushbu qadamlar yordamida **EduQuiz Bot**ni har qanday Linux (Ubuntu/Debian) VPS serveriga xavfsiz va to'liq Dockerize qilingan holda joylashtirishingiz mumkin. Barcha xizmatlar (PostgreSQL, Redis, Backend, Frontend) bitta `docker-compose.yml` orqali ko'tariladi va `systemd` orqali avtomatik nazorat qilinadi.

---

## 1. Serverni tayyorlash
Serverga SSH orqali ulaning:
```bash
ssh root@<SERVER_IP_MANZILI>
```

Tizimni yangilash va kerakli dasturlarni o'rnatish:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw
```

## 2. Docker va Docker Compose o'rnatish
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

## 3. Xavfsizlik va xavfsizlik devori (Firewall)
Faqat zarur portlarni ochamiz:
```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```
*(Y port 80 orqali frontend va admin API ga kiriladi)*

## 4. Loyihani yuklash va sozlash
Yangi `eduquiz` foydalanuvchisi yaratish va loyihani joylash tavsiya qilinadi.
```bash
# 1. Yangi foydalanuvchi yaratish (ixtiyoriy)
sudo adduser eduquiz
sudo su - eduquiz

# 2. Loyihani Github/Gitlab orqali yuklab olish
git clone <LOYIHA_GIT_URL> testbot
cd testbot

# 3. .env faylini yaratish va to'ldirish
cp eduquiz_bot/.env.example eduquiz_bot/.env
nano eduquiz_bot/.env
```
`.env` faylidagi barcha tokenlar va ma'lumotlar to'g'riligini tekshiring (DB, Redis, Bot Token, Gemini API Key).

## 5. Tizim avtomatik ishga tushishi uchun Systemd Service
VPS o'chib yonsa ham tizim doim avtomatik ishlashi uchun `systemd` servisini o'rnatamiz:

```bash
# Servis faylini tizimga nusxalash (root orqali)
sudo cp testbot.service /etc/systemd/system/testbot.service

# Systemd ni yangilash va xizmatni yoqish
sudo systemctl daemon-reload
sudo systemctl enable testbot.service
sudo systemctl start testbot.service
```

## 6. Jurnal va Holatni tekshirish
Bot ishga tushganini tekshirish uchun:
```bash
# Systemd orqali
sudo systemctl status testbot.service

# Yoki to'g'ridan to'g'ri Docker orqali
docker compose ps
docker compose logs -f backend
```

## 7. Qo'shimcha
Agar ma'lumotlar bazasiga ulanish xatosi bersa, `docker compose down -v` orqali eskirgan volumelarni o'chirib, qayta ishlating. Bu barcha joriy bazani o'chiradi, shuning uchun faqat birinchi o'rnatishda qilinadi!
