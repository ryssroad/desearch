"""
Модуль для загрузки переменных окружения из .env файла.
"""
import os
import bittensor as bt
from pathlib import Path

def load_dotenv():
    """
    Загружает переменные окружения из .env файла.
    Ищет файл в текущей директории и родительских директориях.
    
    Returns:
        bool: True, если файл найден и загружен, иначе False.
    """
    try:
        # Пытаемся импортировать python-dotenv
        from dotenv import load_dotenv as _load_dotenv
        
        # Ищем .env файл в текущей директории и вверх по иерархии
        dotenv_path = find_dotenv_file()
        
        if dotenv_path:
            bt.logging.info(f"Загружаем переменные окружения из {dotenv_path}")
            _load_dotenv(dotenv_path)
            return True
        else:
            bt.logging.warning("Файл .env не найден")
            return False
            
    except ImportError:
        bt.logging.warning(
            "Библиотека python-dotenv не установлена. "
            "Установите её с помощью 'pip install python-dotenv' "
            "для загрузки переменных из .env файла."
        )
        return False

def find_dotenv_file():
    """
    Ищет файл .env в текущей директории и вверх по иерархии.
    
    Returns:
        str: Путь к найденному файлу .env или None, если файл не найден.
    """
    current_dir = Path.cwd()
    
    # Ищем .env файл в текущей директории и поднимаемся до 3 уровней вверх
    for _ in range(4):
        env_file = current_dir / ".env"
        if env_file.exists():
            return str(env_file)
        
        # Поднимаемся на уровень выше
        parent_dir = current_dir.parent
        if parent_dir == current_dir:  # Достигли корня файловой системы
            break
        current_dir = parent_dir
    
    return None

def get_env_variable(name, default=None):
    """
    Получает значение переменной окружения с заданным именем.
    Если переменная не найдена, возвращает значение по умолчанию.
    
    Args:
        name (str): Имя переменной окружения
        default: Значение по умолчанию, если переменная не найдена
        
    Returns:
        str: Значение переменной окружения или значение по умолчанию
    """
    return os.environ.get(name, default)
