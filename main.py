"""
Główny plik uruchamiający oba boty jednocześnie
+ serwer HTTP do utrzymywania przy życiu na Render.com
"""
import logging
import asyncio
from threading import Thread
from customer_bot import main as customer_main
from admin_bot import main as admin_main
from keep_alive import keep_alive

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def run_both_bots():
    logger.info("🚀 Uruchamianie obu botów...")
    
    # Uruchom serwer HTTP w osobnym wątku (dla Render.com)
    keep_alive()
    logger.info("✅ Serwer HTTP uruchomiony na porcie 8080")
    
    # Uruchom oba boty asynchronicznie
    customer_task = asyncio.create_task(asyncio.to_thread(customer_main))
    admin_task = asyncio.create_task(asyncio.to_thread(admin_main))
    
    logger.info("✅ Oba boty uruchomione!")
    
    await asyncio.gather(customer_task, admin_task)

if __name__ == '__main__':
    try:
        asyncio.run(run_both_bots())
    except KeyboardInterrupt:
        logger.info("⛔ Zatrzymano boty")