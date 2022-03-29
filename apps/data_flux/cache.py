from apps.core.functions.functions_setups import settings


class CacheRegistry:
    """Registry de cache"""

    def __init__(self):
        """
        Instancie le cache registry, si redis n'est pas importé ni activé,
        alors on cache dans un registry
        """
        self.registry = dict()

        try:
            import redis

            try:
                self.registry = redis.StrictRedis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                )
            except redis.exceptions.ConnectionError:
                raise ModuleNotFoundError

        except ModuleNotFoundError:
            print("ModuleNotFoundError")

    def get(self, name):
        if isinstance(self.registry, (dict,)):
            return self.registry.get(name).encode()
        else:
            self.registry.get(name)

    def set(self, name, value):
        if isinstance(self.registry, (dict,)):
            self.registry[name] = value
        else:
            self.registry.set(name, value)

    def add_error(self, error):
        ...
