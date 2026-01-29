import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8406234881:AAFZIdcHNcidzPDS9gYEPLhVUalbfGCHgF4"
SPREADSHEET_ID = "1kaYGnxOcjX4NSO8FVGCXpXd0Vu61_ydmYRtpykR7Zik"
JSON_KEYFILE = "service_account.json"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
client = gspread.authorize(creds)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Keuangan Aktif\n\n"
        "Perintah:\n"
        "/masuk 100000 gaji\n"
        "/keluar 25000 makan\n"
        "/rekap"
    )

async def simpan_transaksi(update, tipe, jumlah, keterangan):
    user = update.effective_user.first_name
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M")

    sh = client.open_by_key(SPREADSHEET_ID)

    try:
        ws = sh.worksheet(user)
    except:
        ws = sh.add_worksheet(title=user, rows=1000, cols=10)
        ws.append_row(["Tanggal", "Tipe", "Jumlah", "Keterangan", "User"])

    ws.append_row([tanggal, tipe, jumlah, keterangan, user])

async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = update.message.text.split(" ", 2)
        jumlah = int(args[1])
        keterangan = args[2]
        await simpan_transaksi(update, "MASUK", jumlah, keterangan)
        await update.message.reply_text("✅ Pemasukan tercatat")
    except:
        await update.message.reply_text("❌ Format salah\n/masuk 100000 gaji")

async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = update.message.text.split(" ", 2)
        jumlah = int(args[1])
        keterangan = args[2]
        await simpan_transaksi(update, "KELUAR", jumlah, keterangan)
        await update.message.reply_text("✅ Pengeluaran tercatat")
    except:
        await update.message.reply_text("❌ Format salah\n/keluar 25000 makan")

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    sh = client.open_by_key(SPREADSHEET_ID)

    try:
        ws = sh.worksheet(user)
    except:
        await update.message.reply_text("❌ Belum ada data.")
        return

    data = ws.get_all_values()[1:]

    masuk_total = 0
    keluar_total = 0

    for row in data:
        tipe = row[1]
        jumlah = int(row[2])
        if tipe == "MASUK":
            masuk_total += jumlah
        else:
            keluar_total += jumlah

    saldo = masuk_total - keluar_total

    await update.message.reply_text(
        f"📊 Rekap {user}\n"
        f"➕ Masuk: Rp {masuk_total:,}\n"
        f"➖ Keluar: Rp {keluar_total:,}\n"
        f"💰 Saldo: Rp {saldo:,}".replace(",", ".")
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("masuk", masuk))
    app.add_handler(CommandHandler("keluar", keluar))
    app.add_handler(CommandHandler("rekap", rekap))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()


