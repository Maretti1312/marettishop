"""
Główny plik uruchamiający oba boty jednocześnie
+ serwer HTTP do utrzymywania przy życiu na Render.com
"""
import logging
import asyncio
from customer_bot import main as customer_main
from admin_bot import main as admin_main
from keep_alive import keep_alive

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def run_customer_bot():
    """Uruchamia bota klienta w osobnym procesie"""
    try:
        logger.info("🚀 Uruchamianie bota klienta...")
        customer_main()
    except Exception as e:
        logger.error(f"❌ Błąd bota klienta: {e}")

def run_admin_bot():
    """Uruchamia bota admina w osobnym procesie"""
    try:
        logger.info("🚀 Uruchamianie bota admina...")
        admin_main()
    except Exception as e:
        logger.error(f"❌ Błąd bota admina: {e}")

if __name__ == '__main__':
    import threading
    
    logger.info("🚀 Uruchamianie systemu botów...")
    
    # Uruchom serwer HTTP w osobnym wątku (dla Render.com)
    keep_alive()
    logger.info("✅ Serwer HTTP uruchomiony na porcie 8080")
    
    # Uruchom bota klienta w osobnym wątku
    customer_thread = threading.Thread(target=run_customer_bot, daemon=True)
    customer_thread.start()
    logger.info("✅ Bot klienta uruchomiony w wątku")
    
    # Uruchom bota admina w głównym wątku
    logger.info("✅ Uruchamianie bota admina w głównym wątku...")
    run_admin_bot()
