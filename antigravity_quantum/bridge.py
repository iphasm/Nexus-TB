import threading
import asyncio
import time
from .core.engine import QuantumEngine

class QuantumBridge:
    """
    Bridges the Synchronous Telegram Bot (Main Thread) with the 
    Asynchronous Quantum Engine (Background Thread).
    """
    def __init__(self, notification_callback):
        self.engine = QuantumEngine()
        self.loop = None
        self.thread = None
        self.notification_callback = notification_callback # Sync function to call on signal
        self._stop_event = threading.Event()

    def _run_async_loop(self):
        """
        Entry point for the background thread.
        Creates a new event loop and runs the engine.
        """
        print("🌉 QuantumBridge: Starting Background Async Loop...")
        
        # Windows specific policy fix if needed (redundant if main sets it, but safe)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except:
            pass
            
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Setup Callback
        # The engine calls this async function
        async def async_signal_handler(signal):
            # We bridge back to Sync world
            # print(f"🌉 Bridge Received Signal: {signal.symbol}")
            if self.notification_callback:
                try:
                    self.notification_callback(signal)
                except Exception as e:
                    print(f"❌ Bridge Callback Error: {e}")

        self.engine.set_callback(async_signal_handler)
        
        # Run Engine
        try:
            self.loop.run_until_complete(self.engine.run())
        except Exception as e:
            print(f"❌ QuantumBridge Error: {e}")
        finally:
            print("🌉 QuantumBridge: Loop Finished.")

    def start(self):
        if self.thread and self.thread.is_alive():
            print("⚠️ Bridge already running.")
            return

        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.loop:
            print("🛑 Stopping Quantum Bridge...")
            # Schedule stop in the loop
            future = asyncio.run_coroutine_threadsafe(self.engine.stop(), self.loop)
            try:
                future.result(timeout=5)
            except:
                print("⚠️ Stop timeout.")
        
        if self.thread:
            self.thread.join(timeout=2)
