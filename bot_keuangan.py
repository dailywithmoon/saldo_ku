import pandas as pd
import matplotlib.pyplot as plt
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

def get_dataframe_user(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)



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
        
async def rekaphari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = get_username(update)
    sheet = get_user_sheet(username)

    masuk, keluar, saldo = hitung_rekap(sheet, "hari")

    tanggal = datetime.now().strftime("%d-%m-%Y")

    await update.message.reply_text(
        f"📊 Rekap Harian ({tanggal}) - {username}\n\n"
        f"💰 Total Masuk : {masuk}\n"
        f"💸 Total Keluar: {keluar}\n"
        f"🧮 Saldo       : {saldo}"
    )

async def rekapbulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = get_username(update)
    sheet = get_user_sheet(username)

    masuk, keluar, saldo = hitung_rekap(sheet, "bulan")

    bulan = datetime.now().strftime("%B %Y")

    await update.message.reply_text(
        f"📊 Rekap Bulanan ({bulan}) - {username}\n\n"
        f"💰 Total Masuk : {masuk}\n"
        f"💸 Total Keluar: {keluar}\n"
        f"🧮 Saldo       : {saldo}"
    )

async def grafikhari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = get_username(update)
    sheet = get_user_sheet(username)

    df = get_dataframe_user(sheet)

    if df.empty:
        await update.message.reply_text("📭 Belum ada data.")
        return

    # 🔥 Normalisasi kolom
    df.columns = df.columns.str.strip()

    # Paksa jumlah jadi angka
    df["Jumlah"] = (
        df["Jumlah"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    df["Jumlah"] = pd.to_numeric(df["Jumlah"], errors="coerce").fillna(0)

    # Paksa tipe uppercase
    df["Tipe"] = df["Tipe"].astype(str).str.upper().str.strip()

    # Parse tanggal
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df = df.dropna(subset=["Tanggal"])

    df["TanggalOnly"] = df["Tanggal"].dt.date

    # Filter
    masuk = df[df["Tipe"] == "MASUK"].groupby("TanggalOnly")["Jumlah"].sum()
    keluar = df[df["Tipe"] == "KELUAR"].groupby("TanggalOnly")["Jumlah"].sum()

    if masuk.empty and keluar.empty:
        await update.message.reply_text("⚠️ Data tidak terbaca untuk grafik.")
        return

    # Plot
    plt.figure()
    if not masuk.empty:
        masuk.plot(marker="o", label="Masuk")
    if not keluar.empty:
        keluar.plot(marker="o", label="Keluar")

    plt.legend()
    plt.title(f"Grafik Harian - {username}")
    plt.xlabel("Tanggal")
    plt.ylabel("Jumlah")
    plt.tight_layout()

    filename = f"grafik_{username}_harian.png"
    plt.savefig(filename)
    plt.close()

    await update.message.reply_photo(photo=open(filename, "rb"))
    os.remove(filename)


async def grafikbulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = get_username(update)
    sheet = get_user_sheet(username)

    df = get_dataframe_user(sheet)

    if df.empty:
        await update.message.reply_text("📭 Belum ada data.")
        return

    # Normalisasi
    df.columns = df.columns.str.strip()

    df["Jumlah"] = (
        df["Jumlah"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    df["Jumlah"] = pd.to_numeric(df["Jumlah"], errors="coerce").fillna(0)

    df["Tipe"] = df["Tipe"].astype(str).str.upper().str.strip()

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df = df.dropna(subset=["Tanggal"])

    df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)

    masuk = df[df["Tipe"] == "MASUK"].groupby("Bulan")["Jumlah"].sum()
    keluar = df[df["Tipe"] == "KELUAR"].groupby("Bulan")["Jumlah"].sum()

    if masuk.empty and keluar.empty:
        await update.message.reply_text("⚠️ Data tidak terbaca untuk grafik.")
        return

    # Plot
    plt.figure()
    if not masuk.empty:
        masuk.plot(marker="o", label="Masuk")
    if not keluar.empty:
        keluar.plot(marker="o", label="Keluar")

    plt.legend()
    plt.title(f"Grafik Bulanan - {username}")
    plt.xlabel("Bulan")
    plt.ylabel("Jumlah")
    plt.tight_layout()

    filename = f"grafik_{username}_bulanan.png"
    plt.savefig(filename)
    plt.close()

    await update.message.reply_photo(photo=open(filename, "rb"))
    os.remove(filename)

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = get_username(update)
    sheet = get_user_sheet(username)
    df = get_dataframe_user(sheet)

    if df.empty:
        await update.message.reply_text("📭 Tidak ada data untuk di-export.")
        return

    filename = f"export_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df.to_excel(filename, index=False, engine="openpyxl")

    await update.message.reply_document(
        document=open(filename, "rb"),
        filename=filename,
        caption="📊 Data keuangan berhasil di-export."
    )

    os.remove(filename)




def hitung_rekap(sheet, mode="hari"):
    rows = sheet.get_all_values()[1:]  # skip header

    total_masuk = 0
    total_keluar = 0

    now = datetime.now()

    for row in rows:
        try:
            tanggal = datetime.strptime(row[0], "%Y-%m-%d %H:%M")
            tipe = row[1]
            jumlah = int(row[2])

            if mode == "hari":
                if tanggal.date() != now.date():
                    continue

            if mode == "bulan":
                if tanggal.month != now.month or tanggal.year != now.year:
                    continue

            if tipe == "MASUK":
                total_masuk += jumlah
            elif tipe == "KELUAR":
                total_keluar += jumlah

        except:
            continue

    saldo = total_masuk - total_keluar

    return total_masuk, total_keluar, saldo


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("masuk", masuk))
    app.add_handler(CommandHandler("keluar", keluar))
    app.add_handler(CommandHandler("rekaphari", rekaphari))
    app.add_handler(CommandHandler("rekapbulan", rekapbulan))
    app.add_handler(CommandHandler("grafikhari", grafikhari))
    app.add_handler(CommandHandler("grafikbulan", grafikbulan))
    app.add_handler(CommandHandler("export", export_excel))


    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()













