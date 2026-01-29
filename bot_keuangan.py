import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8406234881:AAFZIdcHNcidzPDS9gYEPLhVUalbfGCHgF4"
SPREADSHEET_ID = "1kaYGnxOcjX4NSO8FVGCXpXd0Vu61_ydmYRtpykR7Zik"
JSON_KEYFILE = "service_account.json"

# ===== GOOGLE SHEET SETUP =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

google_creds_json = os.environ.get("GOOGLE_CREDS")
google_creds_dict = json.loads(google_creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_creds_dict, scope
)


client = gspread.authorize(creds)

# GANTI dengan nama spreadsheet kamu
spreadsheet = client.open("Saldo_Ku")

def get_user_sheet(username):
    try:
        return spreadsheet.worksheet(username)
    except:
        ws = spreadsheet.add_worksheet(title=username, rows=1000, cols=10)
        ws.append_row(["Tanggal", "Tipe", "Jumlah", "Keterangan"])
        return ws    

def get_username(update):
    user = update.effective_user
    return user.username or user.first_name


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
        username = get_username(update)
        sheet = get_user_sheet(username)

        jumlah = int(context.args[0])
        keterangan = " ".join(context.args[1:])

        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M")

        sheet.append_row([tanggal, "MASUK", jumlah, keterangan])

        await update.message.reply_text(
            f"✅ Pemasukan dicatat untuk {username}\n"
            f"💰 {jumlah}\n"
            f"📝 {keterangan}"
        )

    except:
        await update.message.reply_text(
            "❌ Format salah\nGunakan: /masuk 100000 gaji"
        )


async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        username = get_username(update)
        sheet = get_user_sheet(username)

        jumlah = int(context.args[0])
        keterangan = " ".join(context.args[1:])

        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M")

        sheet.append_row([tanggal, "KELUAR", jumlah, keterangan])

        await update.message.reply_text(
            f"✅ Pengeluaran dicatat untuk {username}\n"
            f"💸 {jumlah}\n"
            f"📝 {keterangan}"
        )

    except:
        await update.message.reply_text(
            "❌ Format salah\nGunakan: /keluar 50000 makan"
        )


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








