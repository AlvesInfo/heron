"""
ASGI config for heron project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heron.settings')

# Get the Django ASGI application
django_application = get_asgi_application()


async def application(scope, receive, send):
    """
    ASGI application with lifespan protocol support
    """
    if scope['type'] == 'lifespan':
        # Handle lifespan events
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                # Startup event
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                # Shutdown event
                await send({'type': 'lifespan.shutdown.complete'})
                return
    else:
        # Pass other requests to Django
        await django_application(scope, receive, send)
