"""Prompts for the travel agent."""

import yaml
from pathlib import Path

def load_prompts():
    """Load prompts from yaml file."""
    prompts_path = Path(__file__).parent / "prompts.yaml"
    with open(prompts_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Load prompts at module level
PROMPTS = load_prompts()
