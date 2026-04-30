import yaml
from utils.path_tool import get_abs_path
from core.config import settings

def load_config(config_path: str = 'config/settings.yml') -> dict:
    abs_path = get_abs_path(config_path)
    with open(abs_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
conf = load_config()

if __name__ == '__main__':
    print(settings.agent.chat_model_name)
    print(settings.prompts.main_prompt_path)
    
    