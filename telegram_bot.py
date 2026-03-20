#!/usr/bin/env python3
"""
ANC Tracker - Telegram Test Interface

Interactive bot for testing every layer of the ANC tracker stack.
Admin-only: only responds to TELEGRAM_ADMIN_ID.

Required env vars (in .env):
  TELEGRAM_BOT_TOKEN      from @BotFather
  TELEGRAM_ADMIN_ID       your Telegram user ID (get from @userinfobot)
  TRACKER_ENCRYPTION_KEY  32-byte hex key
  DB_PATH                 path to tracker.db
"""

import json
import os
import sqlite3
import subprocess
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters,
)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID  = int(os.environ["TELEGRAM_ADMIN_ID"])
DB_PATH   = os.environ.get("DB_PATH", "data/tracker.db")
LOG_DIR   = os.environ.get("LOG_DIR", "logs")

REG_ID, REG_NAME, REG_PHONE, REG_AGE, REG_VILLAGE, REG_LMP, REG_CONFIRM = range(7)


def admin_only(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("Unauthorized.")
            return
        return await func(update, ctx)
    return wrapper


def get_db():
    return sqlite3.connect(DB_PATH)


@admin_only
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*ANC Tracker Test Interface*\n\n"
        "*Patient management*\n"
        "/register - Register new patient (guided)\n"
        "/patients - List all patients\n"
        "/patient <id> - Patient detail + visit schedule\n\n"
        "*Reminders*\n"
        "/pending - Pending reminders\n"
        "/upcoming - Visits in next 7 days\n"
        "/defaulters - Missed / overdue visits\n"
        "/run\\_dry - Trigger reminder pipeline (DRY\\_RUN=1)\n"
        "/run\\_live - Trigger reminder pipeline (real messages)\n\n"
        "*Messaging test*\n"
        "/send\\_test <patient\\_id> <7day|2day|missed>\n\n"
        "*Encryption*\n"
        "/encrypt <text>\n"
        "/decrypt <hex blob>\n\n"
        "*System*\n"
        "/health - DB stats + cron status\n"
        "/logs - Last 20 lines of today log\n"
        "/cron - Show crontab",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_patients(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    rows = conn.execute(
        "SELECT patient_id, age, village, registration_date, start_date "
        "FROM patients ORDER BY registration_date DESC"
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No patients registered yet.")
        return
    lines = [f"*Patients ({len(rows)})*\n"]
    for r in rows:
        lines.append(f"`{r[0]}` - age {r[1]}, {r[2]} | LMP: {r[4]} Reg: {r[3]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_patient(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /patient <patient_id>")
        return
    pid = ctx.args[0]
    conn = get_db()
    p = conn.execute(
        "SELECT patient_id, name_encrypted, phone_encrypted, age, village, "
        "registration_date, start_date FROM patients WHERE patient_id=?", (pid,)
    ).fetchone()
    if not p:
        conn.close()
        await update.message.reply_text(f"Patient `{pid}` not found.", parse_mode="Markdown")
        return
    visits = conn.execute(
        "SELECT visit_number, visit_name, scheduled_date, status "
        "FROM visits WHERE patient_id=? ORDER BY visit_number", (pid,)
    ).fetchall()
    reminders = conn.execute(
        "SELECT r.reminder_type, r.scheduled_time, r.status "
        "FROM reminders r JOIN visits v ON r.visit_id=v.visit_id "
        "WHERE v.patient_id=? ORDER BY r.scheduled_time", (pid,)
    ).fetchall()
    conn.close()
    try:
        name  = _decrypt(p[1])
        phone = _decrypt(p[2])
    except Exception:
        name = phone = "(decryption failed)"
    status_map = {"pending": "[pending]", "completed": "[done]", "missed": "[MISSED]"}
    lines = [
        f"*Patient {p[0]}*", f"Name: {name}", f"Phone: {phone}",
        f"Age: {p[3]}   Village: {p[4]}", f"LMP: {p[6]}   Registered: {p[5]}",
        "", "*Visits:*",
    ]
    for v in visits:
        lines.append(f"  Visit {v[0]}: {v[1]} - {v[2]} {status_map.get(v[3], v[3])}")
    if reminders:
        lines += ["", "*Reminders:*"]
        for r in reminders:
            lines.append(f"  {r[0]} due {r[1]} ({r[2]})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    rows = conn.execute(
        "SELECT r.reminder_id, p.patient_id, r.reminder_type, r.scheduled_time, v.visit_name "
        "FROM reminders r "
        "JOIN visits v ON r.visit_id = v.visit_id "
        "JOIN patients p ON v.patient_id = p.patient_id "
        "WHERE r.status = 'pending' ORDER BY r.scheduled_time LIMIT 25"
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No pending reminders.")
        return
    lines = [f"*Pending ({len(rows)})*\n"]
    for r in rows:
        lines.append(f"`#{r[0]}` {r[1]} - {r[2]} - {r[4]}\n  Due: {r[3]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_upcoming(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    rows = conn.execute(
        "SELECT patient_id, visit_name, scheduled_date FROM visits "
        "WHERE scheduled_date BETWEEN date('now') AND date('now', '+7 days') "
        "AND status = 'pending' ORDER BY scheduled_date"
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No visits in the next 7 days.")
        return
    lines = ["*Upcoming (next 7 days)*\n"]
    for r in rows:
        lines.append(f"`{r[0]}` - {r[1]} | Date: {r[2]}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_defaulters(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    rows = conn.execute(
        "SELECT patient_id, visit_name, scheduled_date, status FROM visits "
        "WHERE status = 'missed' "
        "OR (status = 'pending' AND scheduled_date < date('now')) "
        "ORDER BY scheduled_date DESC LIMIT 25"
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No defaulters.")
        return
    lines = [f"*Defaulters ({len(rows)})*\n"]
    for r in rows:
        lines.append(f"`{r[0]}` - {r[1]} | Missed: {r[2]} ({r[3]})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def cmd_run_dry(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Running check_reminders.sh with DRY_RUN=1...")
    result = subprocess.run(
        ["bash", "scheduling/check_reminders.sh"], capture_output=True, text=True,
        env={**os.environ, "DRY_RUN": "1", "DB_PATH": DB_PATH}
    )
    tail = _tail_log()
    await update.message.reply_text(
        f"*Dry run complete* (exit {result.returncode})\n\n```\n{tail}\n```",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_run_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("Yes - send real messages", callback_data="run_live_confirm"),
        InlineKeyboardButton("Cancel", callback_data="run_live_cancel"),
    ]]
    await update.message.reply_text(
        "WARNING: This will send *real messages*. Confirm?",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )


async def cb_run_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "run_live_cancel":
        await q.edit_message_text("Cancelled.")
        return
    await q.edit_message_text("Running check_reminders.sh (live)...")
    env = {k: v for k, v in os.environ.items() if k != "DRY_RUN"}
    env["DB_PATH"] = DB_PATH
    result = subprocess.run(
        ["bash", "scheduling/check_reminders.sh"], capture_output=True, text=True, env=env
    )
    tail = _tail_log()
    await q.edit_message_text(
        f"*Live run complete* (exit {result.returncode})\n\n```\n{tail}\n```",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_send_test(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: /send_test <patient_id> <7day|2day|missed>")
        return
    pid, rtype = ctx.args[0], ctx.args[1]
    if rtype not in ("7day", "2day", "missed"):
        await update.message.reply_text("reminder_type must be: 7day, 2day, or missed")
        return
    conn = get_db()
    patient = conn.execute("SELECT phone_encrypted FROM patients WHERE patient_id=?", (pid,)).fetchone()
    visit = conn.execute(
        "SELECT visit_name, scheduled_date FROM visits "
        "WHERE patient_id=? AND status='pending' ORDER BY visit_number LIMIT 1", (pid,)
    ).fetchone()
    conn.close()
    if not patient:
        await update.message.reply_text(f"Patient {pid} not found.")
        return
    try:
        phone = _decrypt(patient[0])
    except Exception as e:
        await update.message.reply_text(f"Decryption failed: {e}")
        return
    visit_name = visit[0] if visit else "Test Visit"
    visit_date = visit[1] if visit else str(datetime.utcnow().date())
    payload = json.dumps({
        "phone": phone,
        "message": f"Reminder: {visit_name} on {visit_date}",
        "patient_id": pid,
        "reminder_type": rtype,
    })
    result = subprocess.run(
        ["python3", "plugins/messaging/whatsapp_send.py"],
        input=payload, capture_output=True, text=True
    )
    output = result.stdout.strip() or result.stderr.strip()
    await update.message.reply_text(
        f"*Send test ({pid}/{rtype}):*\n```\n{output}\n```", parse_mode="Markdown")


@admin_only
async def cmd_encrypt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /encrypt <text>")
        return
    result = subprocess.run(
        ["python3", "core/crypto.py", "encrypt", " ".join(ctx.args)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        await update.message.reply_text(f"Encrypted:\n`{result.stdout.strip()}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Error: {result.stderr.strip()}")


@admin_only
async def cmd_decrypt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /decrypt <hex blob>")
        return
    result = subprocess.run(
        ["python3", "core/crypto.py", "decrypt", ctx.args[0]],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        await update.message.reply_text(f"Decrypted:\n`{result.stdout.strip()}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Error: {result.stderr.strip()}")


@admin_only
async def cmd_health(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    pending  = conn.execute("SELECT COUNT(*) FROM reminders WHERE status='pending'").fetchone()[0]
    sent     = conn.execute("SELECT COUNT(*) FROM reminders WHERE status='sent'").fetchone()[0]
    failed   = conn.execute("SELECT COUNT(*) FROM reminders WHERE status='failed'").fetchone()[0]
    overdue  = conn.execute(
        "SELECT COUNT(*) FROM visits WHERE status='pending' AND scheduled_date < date('now')"
    ).fetchone()[0]
    conn.close()
    cron_out = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    cron_ok  = "yes" if "check_reminders" in cron_out else "NO - not configured"
    db_kb    = os.path.getsize(DB_PATH) // 1024 if os.path.exists(DB_PATH) else 0
    log_f    = f"{LOG_DIR}/reminders_{datetime.utcnow().strftime('%Y%m%d')}.log"
    log_ok   = "exists" if os.path.exists(log_f) else "not yet today"
    await update.message.reply_text(
        f"*System Health*\n"
        f"DB: {db_kb} KB\n"
        f"Patients: {patients}\n"
        f"Pending reminders: {pending}\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}\n"
        f"Overdue visits: {overdue}\n"
        f"Cron: {cron_ok}\n"
        f"Log: {log_ok}",
        parse_mode="Markdown"
    )


@admin_only
async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    log_f = f"{LOG_DIR}/reminders_{datetime.utcnow().strftime('%Y%m%d')}.log"
    if not os.path.exists(log_f):
        await update.message.reply_text("No log file today yet.")
        return
    tail = _tail_log(20)
    await update.message.reply_text(
        f"*Today log (last 20):*\n```\n{tail}\n```", parse_mode="Markdown")


@admin_only
async def cmd_cron(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout.strip()
    await update.message.reply_text(
        f"*Crontab:*\n```\n{out or '(empty)'}\n```", parse_mode="Markdown")


@admin_only
async def cmd_register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Registering a new patient. /cancel at any time.\n\n"
        "*Step 1/6 - Patient ID* (e.g. P004):",
        parse_mode="Markdown"
    )
    return REG_ID


async def step_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pid = update.message.text.strip()
    conn = get_db()
    exists = conn.execute("SELECT 1 FROM patients WHERE patient_id=?", (pid,)).fetchone()
    conn.close()
    if exists:
        await update.message.reply_text(f"`{pid}` already exists. Choose another:", parse_mode="Markdown")
        return REG_ID
    ctx.user_data["patient_id"] = pid
    await update.message.reply_text("*Step 2/6 - Full name:*", parse_mode="Markdown")
    return REG_NAME


async def step_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("*Step 3/6 - Phone* (+91XXXXXXXXXX):", parse_mode="Markdown")
    return REG_PHONE


async def step_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.startswith("+"):
        await update.message.reply_text("Must start with + (e.g. +91...). Try again:")
        return REG_PHONE
    ctx.user_data["phone"] = phone
    await update.message.reply_text("*Step 4/6 - Age (years):*", parse_mode="Markdown")
    return REG_AGE


async def step_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text.strip())
        if not (10 <= age <= 60):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Enter a valid age (10-60):")
        return REG_AGE
    ctx.user_data["age"] = age
    await update.message.reply_text("*Step 5/6 - Village:*", parse_mode="Markdown")
    return REG_VILLAGE


async def step_village(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["village"] = update.message.text.strip()
    await update.message.reply_text("*Step 6/6 - LMP date* (YYYY-MM-DD):", parse_mode="Markdown")
    return REG_LMP


async def step_lmp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lmp = update.message.text.strip()
    try:
        datetime.strptime(lmp, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Invalid format. Use YYYY-MM-DD:")
        return REG_LMP
    ctx.user_data["lmp"] = lmp
    d = ctx.user_data
    keyboard = [[
        InlineKeyboardButton("Confirm", callback_data="reg_confirm"),
        InlineKeyboardButton("Cancel",  callback_data="reg_cancel"),
    ]]
    await update.message.reply_text(
        f"*Confirm:*\n"
        f"ID: `{d['patient_id']}`\n"
        f"Name: {d['name']}\n"
        f"Phone: {d['phone']}\n"
        f"Age: {d['age']}\n"
        f"Village: {d['village']}\n"
        f"LMP: {d['lmp']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return REG_CONFIRM


async def cb_reg_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "reg_cancel":
        ctx.user_data.clear()
        await q.edit_message_text("Cancelled.")
        return ConversationHandler.END
    d = ctx.user_data
    result = subprocess.run(
        ["python3", "core/register_patient.py",
         "--patient-id", d["patient_id"],
         "--name",       d["name"],
         "--phone",      d["phone"],
         "--age",        str(d["age"]),
         "--village",    d["village"],
         "--lmp",        d["lmp"]],
        capture_output=True, text=True,
        env={**os.environ, "DB_PATH": DB_PATH}
    )
    msg = result.stdout.strip() if result.returncode == 0 else f"Failed: {result.stderr.strip()}"
    await q.edit_message_text(msg)
    ctx.user_data.clear()
    return ConversationHandler.END


async def reg_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END


def _decrypt(hex_blob) -> str:
    if isinstance(hex_blob, (bytes, bytearray)):
        hex_blob = hex_blob.decode("ascii", errors="replace")
    result = subprocess.run(
        ["python3", "core/crypto.py", "decrypt", str(hex_blob)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _tail_log(lines: int = 20) -> str:
    log_f = f"{LOG_DIR}/reminders_{datetime.utcnow().strftime('%Y%m%d')}.log"
    if not os.path.exists(log_f):
        return "(no log yet today)"
    return subprocess.run(["tail", f"-{lines}", log_f], capture_output=True, text=True).stdout.strip() or "(empty)"


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("register", cmd_register)],
        states={
            REG_ID:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_id)],
            REG_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_name)],
            REG_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_phone)],
            REG_AGE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_age)],
            REG_VILLAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_village)],
            REG_LMP:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_lmp)],
            REG_CONFIRM: [CallbackQueryHandler(cb_reg_confirm, pattern="^reg_")],
        },
        fallbacks=[CommandHandler("cancel", reg_cancel)],
    )
    app.add_handler(reg_conv)
    for cmd, handler in [
        ("start", cmd_start), ("help", cmd_start), ("patients", cmd_patients),
        ("patient", cmd_patient), ("pending", cmd_pending), ("upcoming", cmd_upcoming),
        ("defaulters", cmd_defaulters), ("run_dry", cmd_run_dry), ("run_live", cmd_run_live),
        ("send_test", cmd_send_test), ("encrypt", cmd_encrypt), ("decrypt", cmd_decrypt),
        ("health", cmd_health), ("logs", cmd_logs), ("cron", cmd_cron),
    ]:
        app.add_handler(CommandHandler(cmd, handler))
    app.add_handler(CallbackQueryHandler(cb_run_live, pattern="^run_live_"))
    print(f"Bot started. Admin: {ADMIN_ID}")
    app.run_polling()


if __name__ == "__main__":
    main()
