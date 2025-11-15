"""
Główny plik uruchamiający oba boty jednocześnie
+ serwer HTTP do utrzymywania przy życiu na Render.com
"""
import logging
from threading import Thread
from customer_bot import main as customer_main
from admin_bot import main as admin_main
from keep_alive import keep_alive

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("🚀 Uruchamianie systemu botów...")
    
    # Uruchom serwer HTTP w osobnym wątku (dla Render.com)
    Thread(target=keep_alive, daemon=True).start()
    logger.info("✅ Serwer HTTP uruchomiony na porcie 8080")
    
    # Uruchom bota klienta w osobnym wątku
    customer_thread = Thread(target=customer_main, daemon=True)
    customer_thread.start()
    logger.info("✅ Bot klienta uruchomiony w wątku")
    
    # Uruchom bota admina w głównym wątku (blokujące)
    logger.info("✅ Uruchamianie bota admina w głównym wątku...")
    try:
        admin_main()
    except KeyboardInterrupt:
        logger.info("⛔ Zatrzymano boty")
    except Exception as e:
        logger.error(f"❌ Błąd: {e}")
        raise
