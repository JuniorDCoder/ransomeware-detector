import os
import time
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


class RansomwareTelegramBot:
    def __init__(self, token: str, server_url: str = "http://localhost:5000"):
        self.token = token
        self.server_url = server_url
        self.authorized_users = set()
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Telegram command list can be set via BotFather or by calling set_my_commands asynchronously.

        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            self.authorized_users.add(user_id)

            welcome_message = (
                "Ransomware Detection Bot\n\n"
                "Commands:\n"
                "/status - Current system status\n"
                "/alerts - Recent security alerts\n"
                "/devices - List all monitored devices\n"
                "/stats - Detailed statistics\n"
                "/scan - Scan external device\n"
                "/isolate - Isolate compromised device\n"
                "/help - Show this message again"
            )

            keyboard = [
                [
                    InlineKeyboardButton("Status", callback_data="status"),
                    InlineKeyboardButton("Alerts", callback_data="alerts"),
                ],
                [
                    InlineKeyboardButton("Devices", callback_data="devices"),
                    InlineKeyboardButton("Stats", callback_data="stats"),
                ],
                [
                    InlineKeyboardButton("Scan USB", callback_data="scan"),
                    InlineKeyboardButton("Isolate", callback_data="isolate"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)

        async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not self.is_authorized(update):
                await update.message.reply_text("Unauthorized")
                return
            try:
                response = requests.get(f"{self.server_url}/api/stats", timeout=5)
                if response.status_code == 200:
                    stats = response.json()
                    message = (
                        "System Status\n\n"
                        f"Agents Online: {stats.get('agents_online', 0)}\n"
                        f"Total Alerts: {stats.get('total_alerts', 0)}\n"
                        f"Critical: {stats.get('alerts_by_level', {}).get('CRITICAL', 0)}\n"
                        f"Warning: {stats.get('alerts_by_level', {}).get('WARNING', 0)}\n"
                        f"Info: {stats.get('alerts_by_level', {}).get('INFO', 0)}\n"
                        f"Avg Risk Score: {stats.get('average_risk_score', 0):.1f}\n\n"
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("Failed to get status")
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")

        async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not self.is_authorized(update):
                return
            try:
                response = requests.get(f"{self.server_url}/api/alerts/recent?limit=5")
                if response.status_code == 200:
                    alerts_list = response.json().get("alerts", [])
                    if not alerts_list:
                        await update.message.reply_text("No recent alerts")
                        return
                    message = "Recent Alerts\n\n"
                    for alert in alerts_list:
                        time_str = datetime.fromtimestamp(alert.get("timestamp", 0)).strftime("%H:%M:%S")
                        message += (
                            f"Level: {alert.get('level')}\n"
                            f"Message: {alert.get('message')}\n"
                            f"Time: {time_str}\n"
                            f"Agent: {alert.get('agent_id', 'unknown')}\n\n"
                        )
                    await update.message.reply_text(message)
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")

        async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await status(update, context)

        async def devices(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not self.is_authorized(update):
                return
            try:
                response = requests.get(f"{self.server_url}/api/agents")
                if response.status_code == 200:
                    agents = response.json().get("agents", {})
                    if not agents:
                        await update.message.reply_text("No devices connected")
                        return
                    message = "Connected Devices\n\n"
                    for device_id, info in agents.items():
                        last_seen = info.get("last_seen", 0)
                        status_text = "Online" if (time.time() - last_seen) < 60 else "Offline"
                        message += (
                            f"Device: {device_id}\n"
                            f"Status: {status_text}\n"
                            f"Last seen: {datetime.fromtimestamp(last_seen).strftime('%H:%M:%S')}\n"
                            f"Alerts: {info.get('data', {}).get('stats', {}).get('alert_count', 0)}\n\n"
                        )
                    await update.message.reply_text(message)
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")

        async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not self.is_authorized(update):
                return
            devices = [
                {"id": "usb1", "name": "USB Drive"},
                {"id": "usb2", "name": "External HDD"},
            ]
            keyboard = [
                [InlineKeyboardButton(f"Scan {d['name']}", callback_data=f"scan_{d['id']}")]
                for d in devices
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Select device to scan:", reply_markup=reply_markup)

        async def isolate(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not self.is_authorized(update):
                return
            try:
                response = requests.get(f"{self.server_url}/api/agents")
                if response.status_code == 200:
                    agents = response.json().get("agents", {})
                    keyboard = [
                        [InlineKeyboardButton(f"Isolate {device_id}", callback_data=f"isolate_{device_id}")]
                        for device_id in agents.keys()
                    ]
                    if keyboard:
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text("Select device to isolate:", reply_markup=reply_markup)
                    else:
                        await update.message.reply_text("No devices to isolate")
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")

        async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            data = query.data

            if data.startswith("scan_"):
                device_id = data[5:]
                await query.edit_message_text(text=f"Scanning {device_id}...")
            elif data.startswith("isolate_"):
                device_id = data[8:]
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data=f"confirm_isolate_{device_id}"),
                        InlineKeyboardButton("No", callback_data="cancel"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"Confirm isolation for {device_id}?", reply_markup=reply_markup
                )
            elif data.startswith("confirm_isolate_"):
                device_id = data[15:]
                try:
                    response = requests.post(
                        f"{self.server_url}/api/device/{device_id}/isolate",
                        json={"command": "isolate", "source": "telegram"},
                    )
                    if response.status_code == 200:
                        await query.edit_message_text(f"Device {device_id} isolated")
                    else:
                        await query.edit_message_text(f"Failed to isolate {device_id}")
                except Exception as e:
                    await query.edit_message_text(f"Error: {str(e)}")
            elif data == "cancel":
                await query.edit_message_text("Action cancelled")
            elif data == "status":
                await status(update, context)
            elif data == "alerts":
                await alerts(update, context)
            elif data == "devices":
                await devices(update, context)
            elif data == "stats":
                await stats(update, context)

        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            help_text = (
                "Commands:\n"
                "/start - Initialize bot\n"
                "/status - Current system status\n"
                "/alerts - Recent security alerts\n"
                "/devices - List monitored devices\n"
                "/stats - Detailed statistics\n"
                "/scan - Scan external device\n"
                "/isolate - Isolate compromised device\n"
                "/help - Show this message"
            )
            await update.message.reply_text(help_text)

        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CommandHandler("status", status))
        self.application.add_handler(CommandHandler("alerts", alerts))
        self.application.add_handler(CommandHandler("devices", devices))
        self.application.add_handler(CommandHandler("scan", scan))
        self.application.add_handler(CommandHandler("isolate", isolate))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("stats", stats))
        self.application.add_handler(CallbackQueryHandler(button_callback))

    def is_authorized(self, update: Update) -> bool:
        return update.effective_user.id in self.authorized_users

    def run(self):
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set")
    RansomwareTelegramBot(token).run()
