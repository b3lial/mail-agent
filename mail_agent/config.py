from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class ProxyConfig:
    base_url: str
    api_key: str


@dataclass
class LLMConfig:
    model: str = "llama3.2"
    base_url: str = "http://127.0.0.1:11434"


@dataclass
class AgentConfig:
    poll_interval: int = 300
    folder: Optional[str] = None
    instructions: str = "- Mark all emails as read"


@dataclass
class Config:
    proxy: ProxyConfig
    llm: LLMConfig
    agent: AgentConfig

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> "Config":
        with open(path) as f:
            data = yaml.safe_load(f)

        proxy = ProxyConfig(**data["proxy"])
        llm = LLMConfig(**data.get("llm", {}))
        agent = AgentConfig(**data.get("agent", {}))
        return cls(proxy=proxy, llm=llm, agent=agent)
