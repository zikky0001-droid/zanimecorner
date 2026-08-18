"""
DEV ZIKKY TELEGRAM - Command Loader
"""

import importlib
from pathlib import Path

COMMANDS = {}
ALIASES = {}

def load_commands():
    """Load all commands from commands folder"""
    global COMMANDS, ALIASES
    
    command_folders = ['general', 'admin', 'owner', 'utility', 'media', 'fun', 'ai']
    base_path = Path(__file__).parent.parent / 'commands'
    
    loaded_count = 0
    failed_count = 0
    skipped_count = 0
    
    for folder in command_folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            continue
        
        for file_path in folder_path.glob('*.py'):
            # Skip __init__.py files
            if file_path.name == '__init__.py':
                skipped_count += 1
                continue
            
            module_name = f"commands.{folder}.{file_path.stem}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Check if it's a valid command module
                if not hasattr(module, 'COMMAND_NAME'):
                    print(f"⏭️ Skipping {file_path.name}: No COMMAND_NAME defined")
                    skipped_count += 1
                    continue
                
                if not hasattr(module, 'execute'):
                    print(f"⏭️ Skipping {file_path.name}: No execute function")
                    skipped_count += 1
                    continue
                
                command_name = getattr(module, 'COMMAND_NAME', file_path.stem)
                
                # Store the command
                COMMANDS[command_name] = {
                    'name': command_name,
                    'aliases': getattr(module, 'ALIASES', []),
                    'description': getattr(module, 'DESCRIPTION', ''),
                    'category': folder,
                    'admin_only': getattr(module, 'ADMIN_ONLY', False),
                    'owner_only': getattr(module, 'OWNER_ONLY', False),
                    'group_only': getattr(module, 'GROUP_ONLY', False),
                    'private_only': getattr(module, 'PRIVATE_ONLY', False),
                    'bot_admin_needed': getattr(module, 'BOT_ADMIN_NEEDED', False),
                    'function': getattr(module, 'execute')
                }
                
                # Register aliases
                for alias in COMMANDS[command_name]['aliases']:
                    ALIASES[alias] = command_name
                
                loaded_count += 1
                print(f"✅ Loaded command: {command_name} ({folder})")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Failed to load {file_path.name}: {e}")
    
    print(f"\n📊 Command Load Summary: {loaded_count} loaded, {failed_count} failed, {skipped_count} skipped")
    return COMMANDS

def get_command(command_name):
    """Get command by name (including aliases)"""
    # Check direct command
    if command_name in COMMANDS:
        return COMMANDS[command_name]
    
    # Check alias
    if command_name in ALIASES:
        return COMMANDS[ALIASES[command_name]]
    
    # ✅ Fallback: If command not found, return None
    return None

def get_commands_by_category(category):
    """Get all commands in a category"""
    return {name: info for name, info in COMMANDS.items() if info.get('category') == category}
    