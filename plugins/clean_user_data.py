import asyncio
from plugins.anime import user_data
import time

async def cleanup_task():
    while True:
        await asyncio.sleep(600)  # Check every 10 minutes
        current_time = time.time()
        # Find entries older than 30 minutes
        to_delete = []
        for user_id, data in list(user_data.items()):
            if current_time - data.get('timestamp', 0) > 1800:
                to_delete.append(user_id)

        for user_id in to_delete:
            del user_data[user_id]
