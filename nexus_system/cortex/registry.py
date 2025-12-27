"""
Strategy Registry: Auto-discovers and registers all IStrategy implementations.
Enables plug-and-play strategy system without modifying factory.py.
"""

import os
import importlib
import inspect
from typing import Dict, Type, Optional
from .base import IStrategy


class StrategyRegistry:
    """
    Dynamic Strategy Registry.
    Scans the cortex directory and registers all classes inheriting from IStrategy.
    """
    _registry: Dict[str, Type[IStrategy]] = {}
    _initialized: bool = False

    @classmethod
    def _discover_strategies(cls):
        """
        Scans the cortex directory for strategy modules.
        Registers any class that inherits from IStrategy.
        """
        if cls._initialized:
            return
            
        cortex_dir = os.path.dirname(__file__)
        
        # Files to skip (not strategies)
        skip_files = {'__init__.py', 'base.py', 'factory.py', 'registry.py', 
                      'classifier.py', 'ml_classifier.py'}
        
        for filename in os.listdir(cortex_dir):
            if not filename.endswith('.py') or filename in skip_files:
                continue
                
            module_name = filename[:-3]  # Remove .py
            
            try:
                # Import the module
                module = importlib.import_module(f'.{module_name}', package='nexus_system.cortex')
                
                # Find all IStrategy subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, IStrategy) and obj is not IStrategy:
                        # Register by class name
                        cls._registry[name] = obj
                        # Also register by strategy name property if available
                        try:
                            instance = obj()
                            if hasattr(instance, 'name'):
                                cls._registry[instance.name] = obj
                        except:
                            pass  # Some strategies may require args
                            
            except Exception as e:
                print(f"⚠️ Registry: Failed to load {module_name}: {e}")
        
        cls._initialized = True
        print(f"📦 Strategy Registry: Discovered {len(cls._registry)} strategies")

    @classmethod
    def get(cls, name: str) -> Optional[Type[IStrategy]]:
        """
        Get a strategy class by name.
        Returns None if not found.
        """
        cls._discover_strategies()
        return cls._registry.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, Type[IStrategy]]:
        """
        Get all registered strategy classes.
        """
        cls._discover_strategies()
        return cls._registry.copy()

    @classmethod
    def list_names(cls) -> list:
        """
        List all registered strategy names.
        """
        cls._discover_strategies()
        return list(cls._registry.keys())

    @classmethod
    def instantiate(cls, name: str) -> Optional[IStrategy]:
        """
        Get an instance of a strategy by name.
        """
        strategy_cls = cls.get(name)
        if strategy_cls:
            return strategy_cls()
        return None
