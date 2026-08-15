"""Modular Sports Package.
Automatically imports all sport modules so they self-register in SportRegistry.
"""
import importlib
import pkgutil

# Auto-discover all sport plugins in this folder
for _, module_name, is_pkg in pkgutil.iter_modules(__path__):
    if is_pkg and not module_name.startswith('_'):
        importlib.import_module(f"sports.{module_name}")
