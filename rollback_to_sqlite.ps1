# ============================================
# EduQuiz Bot — SQLite ga qaytarish (Rollback)
# ============================================
# Agar PostgreSQL ishlamasa, shu faylni ishga tushiring:
# powershell -ExecutionPolicy Bypass -File rollback_to_sqlite.ps1

Write-Host "🔄 SQLite ga qaytarilmoqda..." -ForegroundColor Yellow

$botDir = "c:\Users\ids\test bot\eduquiz_bot"

# 1. .env ni qaytarish
if (Test-Path "$botDir\.env.sqlite.bak") {
    Copy-Item "$botDir\.env.sqlite.bak" "$botDir\.env" -Force
    Write-Host "✅ .env faylı qaytarildi (SQLite URL)" -ForegroundColor Green
} else {
    Write-Host "❌ .env.sqlite.bak topilmadi!" -ForegroundColor Red
}

# 2. Ma'lumotlar bazasini qaytarish
if (Test-Path "$botDir\eduquiz.db.backup") {
    Copy-Item "$botDir\eduquiz.db.backup" "$botDir\eduquiz.db" -Force
    Write-Host "✅ eduquiz.db qaytarildi (eski ma'lumotlar)" -ForegroundColor Green
} else {
    Write-Host "❌ eduquiz.db.backup topilmadi!" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ ROLLBACK TUGADI! Botni endi SQLite bilan ishga tushirishingiz mumkin." -ForegroundColor Green
Write-Host "   Botni qayta ishga tushirish uchun: python -m app.main" -ForegroundColor Cyan
