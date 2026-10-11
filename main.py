import re, sqlite3, os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
TOKEN = os.environ.get("TOKEN")
conn = sqlite3.connect("dompet.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS transaksi (tanggal TEXT, tipe TEXT, jumlah INTEGER, deskripsi TEXT)")
def parse(text):
    low=text.lower()
    m=re.search(r'(\d+)\s*(rb|ribu|k)?',low)
    if not m: return None
    angka=int(m.group(1))
    if m.group(2) or angka<1000: angka=angka*1000 if angka<1000 else angka
    tipe="MASUK" if any(k in low for k in ["dapat","masuk","gajian"]) else "KELUAR"
    return tipe,angka,text
async def catat(update,context):
    if update.message.text.startswith('/'): return
    hasil=parse(update.message.text)
    if not hasil:
        await update.message.reply_text("Contoh: mi ayam 30rb");return
    tipe,jumlah,desk=hasil
    tgl=datetime.now().strftime("%d-%m %H:%M")
    conn.execute("INSERT INTO transaksi VALUES (?,?,?,?)",(tgl,tipe,jumlah,desk));conn.commit()
    await update.message.reply_text(f"✅ Dicatat {tipe} Rp {jumlah:,}\n{desk}")
async def laporan(update,context):
    masuk=conn.execute("SELECT SUM(jumlah) FROM transaksi WHERE tipe='MASUK'").fetchone()[0] or 0
    keluar=conn.execute("SELECT SUM(jumlah) FROM transaksi WHERE tipe='KELUAR'").fetchone()[0] or 0
    await update.message.reply_text(f"📊 DOMPET LU\nMasuk: Rp {masuk:,}\nKeluar: Rp {keluar:,}\nSisa: Rp {masuk-keluar:,}")
app=Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("laporan",laporan))
app.add_handler(CommandHandler("saldo",laporan))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,catat))
app.run_polling()
