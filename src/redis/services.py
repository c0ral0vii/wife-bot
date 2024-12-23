from redis.asyncio import Redis
from src.config.config import settings


class RedisManager:
    def __init__(self, host: str = "localhost", port: int = 6379, password: str = None):
        """
        Инициализация клиента Redis.
        """
        self.redis = Redis(host=host, port=port, password=password)


    async def get_redis(self):
        return self.redis
    
    async def set_with_ttl(self, key: str, value: str, ttl: int):
        """
        Установить строку с временем жизни (в секундах).
        :param key: Ключ.
        :param value: Значение.
        :param ttl: Время жизни ключа в секундах.
        """
        try:
            await self.redis.set(key, value, ex=ttl)
        except Exception as e:
            print(f"Ошибка при установке ключа {key}: {e}")

    async def get(self, key: str):
        """
        Получить значение по ключу.
        :param key: Ключ.
        :return: Значение строки или None, если ключ отсутствует.
        """
        try:
            value = await self.redis.get(key)
            return value.decode("utf-8") if value else None
        except Exception as e:
            print(f"Ошибка при получении ключа {key}: {e}")
            return None

    async def delete(self, key: str):
        """
        Удалить ключ из Redis.
        :param key: Ключ.
        :return: True, если ключ успешно удалён, иначе False.
        """
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            print(f"Ошибка при удалении ключа {key}: {e}")
            return False

    async def close(self):
        """
        Закрыть соединение с Redis.
        """
        try:
            await self.redis.close()
        except Exception as e:
            print(f"Ошибка при закрытии соединения с Redis: {e}")


# Создаём глобальный объект RedisManager
redis_manager = RedisManager(
    host=settings.RD_HOST,
    port=settings.RD_PORT,
    password=settings.RD_PASS,
)
