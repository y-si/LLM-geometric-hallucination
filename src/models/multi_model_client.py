"""Multi-model client abstraction.

Unified interface for OpenAI, Anthropic, and Together AI models.
"""

import os
from typing import Optional, Dict, Any
import anthropic
from openai import OpenAI


class MultiModelClient:
    """Unified client for multiple LLM providers."""
    
    def __init__(self, provider: str, model_name: str):
        """
        Initialize client for specified provider.
        
        Args:
            provider: 'openai', 'anthropic', or 'together'
            model_name: Model identifier
        """
        self.provider = provider.lower()
        self.model_name = model_name
        
        # Add explicit timeout (60 seconds) to prevent infinite hangs
        if self.provider == 'openai':
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'), timeout=60.0)
        elif self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'), timeout=60.0)
        elif self.provider == 'together':
            # Together uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=os.environ.get('TOGETHER_API_KEY'),
                base_url='https://api.together.xyz/v1',
                timeout=60.0
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.0, system_prompt: str = None) -> str:
        """Generate text completion.

        Args:
            prompt: User message text.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt prepended to the conversation.
        """
        try:
            if self.provider == 'anthropic':
                kwargs = {
                    "model": self.model_name,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}]
                }
                if system_prompt:
                    kwargs["system"] = system_prompt
                response = self.client.messages.create(**kwargs)
                return response.content[0].text
            else:
                # OpenAI and Together use same API
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                # Newer OpenAI models (o1, gpt-4o) prefer max_completion_tokens
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                except Exception as e:
                    if "max_tokens" in str(e) and "max_completion_tokens" in str(e):
                        # Retry with max_completion_tokens
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            max_completion_tokens=max_tokens,
                            temperature=temperature
                        )
                    else:
                        raise e

                return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating with {self.provider}/{self.model_name}: {e}")
            raise
    
    def __repr__(self):
        return f"MultiModelClient(provider='{self.provider}', model='{self.model_name}')"


import yaml
from pathlib import Path

def load_model_config(config_path: str = "experiments/multi_model_config.yaml") -> Dict[str, Dict[str, str]]:
    """Load model configurations from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        model_map = {}
        for model in config.get('models', []):
            model_map[model['name']] = {
                'provider': model['provider'],
                'model': model['model_id']
            }
        return model_map
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return {}

def get_model_client(model_key: str, config_path: str = "experiments/multi_model_config.yaml") -> MultiModelClient:
    """Get a configured model client by key."""
    model_configs = load_model_config(config_path)
    
    if model_key not in model_configs:
        # Fallback to hardcoded defaults if config fails or key missing
        defaults = {
            'gpt-4o-mini': {'provider': 'openai', 'model': 'gpt-4o-mini'},
            'gpt-3.5-turbo': {'provider': 'openai', 'model': 'gpt-3.5-turbo'},
        }
        if model_key in defaults:
            config = defaults[model_key]
            return MultiModelClient(provider=config['provider'], model_name=config['model'])
            
        raise ValueError(f"Unknown model: {model_key}. Available in config: {list(model_configs.keys())}")
    
    config = model_configs[model_key]
    return MultiModelClient(provider=config['provider'], model_name=config['model'])


if __name__ == "__main__":
    # Test different providers
    import sys
    
    test_prompt = "What is 2+2?"
    
    print("Testing multi-model clients...\n")
    
    # Test a few models if API keys are available
    test_models = ['gpt-4o-mini']  # Safe default
    
    if os.getenv('ANTHROPIC_API_KEY'):
        test_models.append('claude-3-5-haiku')
    
    if os.getenv('TOGETHER_API_KEY'):
        test_models.append('llama-3.1-8b')
    
    for model_key in test_models:
        try:
            print(f"Testing {model_key}...")
            client = get_model_client(model_key)
            response = client.generate(test_prompt, max_tokens=50)
            print(f"  Response: {response[:100]}...")
            print(f"  ✓ Success\n")
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
