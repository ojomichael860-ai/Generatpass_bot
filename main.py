import os
import asyncio
import threading
import secrets
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Web Server for Render Health Checks ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Password Generator Bot is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

# --- Password Generator Core Logic ---
def generate_secure_password(length: int) -> str:
    """Generates a cryptographically secure random password."""
    # Enforce minimum characters for structural security
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Combined pool
    all_characters = lower + upper + digits + symbols
    
    # Guarantee at least one character from each set to prevent weak strings
    password = [
        secrets.choice(lower),
        secrets.choice(upper),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    # Fill the remaining length randomly from the entire pool
    password += [secrets.choice(all_characters) for _ in range(length - 4)]
    
    # Shuffle the list securely to mix up the guaranteed characters
    secrets.SystemRandom().shuffle(password)
    
    return "".join(password)

# --- Bot Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome message and shows character length options."""
    keyboard = [
        [
            InlineKeyboardButton("8 Chars (Weak) ⚠️", callback_data="gen_8"),
            InlineKeyboardButton("12 Chars (Good) 👍", callback_data="gen_12")
        ],
        [
            InlineKeyboardButton("16 Chars (Strong) 💪", callback_data="gen_16"),
            InlineKeyboardButton("24 Chars (Military) 🪖", callback_data="gen_24")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 **Welcome to the Secure Password Generator Bot!**\n\n"
        "I create cryptographically strong, randomized passwords to protect your "
        "Social Media, Bank, and Web3 accounts from brute-force hacking.\n\n"
        "**Select the desired password length below:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes interactive click menu calls and sends the generated password."""
    query = update.callback_query
    await query.answer() # Acknowledge the callback click immediately
    
    # Extract the numerical character length from callback_data (e.g. "gen_16" -> 16)
    length = int(query.data.split("_")[1])
    
    # Generate the cryptographically secure password
    new_password = generate_secure_password(length)
    
    # Format the password inside fixed-width code blocks so users can click to copy it easily
    response_text = (
        f"✅ **Generated Secure Password ({length} Characters):**\n\n"
        f"`{new_password}`\n\n"
        f"💡 *Tip: Tap the password block above to copy it instantly. Never share your passwords with anyone!*"
    )
    
    # Remake the keyboard markup to allow generating another one easily
    keyboard = [
        [
            InlineKeyboardButton("Generate Another 🔄", callback_data=f"gen_{length}"),
            InlineKeyboardButton("Change Length ⚙️", callback_data="show_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=response_text, reply_markup=reply_markup, parse_mode="Markdown")

async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Brings back the original configuration settings menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("8 Chars (Weak) ⚠️", callback_data="gen_8"),
            InlineKeyboardButton("12 Chars (Good) 👍", callback_data="gen_12")
        ],
        [
            InlineKeyboardButton("16 Chars (Strong) 💪", callback_data="gen_16"),
            InlineKeyboardButton("24 Chars (Military) 🪖", callback_data="gen_24")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="**Select the desired password length below:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- Main Runtime Routine ---
async def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_TOKEN environment target variable.")

    # Run the essential lightweight health port loop for Render
    threading.Thread(target=run_health_server, daemon=True).start()

    # Initialize the app container
    app = Application.builder().token(TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    
    # Callback query button handlers
    app.add_handler(CallbackQueryHandler(return_to_menu, pattern="^show_menu$"))
    app.add_handler(CallbackQueryHandler(button_click_handler, pattern="^gen_"))
    
    print("Password Generator Bot core pooling engine running...")
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
