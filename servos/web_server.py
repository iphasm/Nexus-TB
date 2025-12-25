
import asyncio
import logging
import os
from aiohttp import web

logger = logging.getLogger(__name__)

async def start_web_server():
    """
    Start a simple aiohttp web server to serve static documentation files.
    """
    try:
        app = web.Application()
        
        # Determine paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_dir = os.path.join(base_dir, 'DOCUMENTACIÓN')
        
        # Route to serve index.html at root
        async def handle_index(request):
            return web.FileResponse(os.path.join(docs_dir, 'index.html'))
            
        app.router.add_get('/', handle_index)
        
        # Serve static files from DOCUMENTACIÓN for CSS, images
        app.router.add_static('/', docs_dir, show_index=True)
        
        # Get port from env (Railway provides PORT)
        port = int(os.environ.get("PORT", 8080))
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🌍 Web Server started on port {port} (Serving {docs_dir})")
        
        # Keep alive
        return runner
        
    except Exception as e:
        logger.error(f"❌ Failed to start Web Server: {e}")
        return None
