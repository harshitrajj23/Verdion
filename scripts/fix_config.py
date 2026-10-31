import os

path = r'c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\backend\app\core\config.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_target = """from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )"""

new_target = """import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )"""

# Handle both CRLF and LF
if old_target.replace("\n", "\r\n") in text:
    text = text.replace(old_target.replace("\n", "\r\n"), new_target.replace("\n", "\r\n"))
elif old_target in text:
    text = text.replace(old_target, new_target)
else:
    print("Target not found!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated config.py successfully!")

