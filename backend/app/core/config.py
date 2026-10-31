from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "VERIDION Decentralized Legal Intelligence Protocol"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./veridion.db"

    # Blockchain
    CHAIN_ID: int = 11155111
    RPC_URL: str = "http://127.0.0.1:8545"
    EVALUATOR_ADDRESS: str = "0x1234567890123456789012345678901234567890"
    ADMIN_ADDRESS: str = "0x0987654321098765432109876543210987654321"

    # Contracts (Default to Sepolia verified deployments)
    CASE_REGISTRY_ADDRESS: str = "0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E"
    AGENT_REGISTRY_ADDRESS: str = "0x32d5D291e287fF173F803f5ee53Aef75BADb2006"
    PREDICTION_MARKET_ADDRESS: str = "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27"
    EVIDENCE_BOUNTY_ADDRESS: str = "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46"
    REPUTATION_SETTLEMENT_ADDRESS: str = "0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c"
    SEPOLIA_RPC_URL: str = "https://ethereum-sepolia-rpc.publicnode.com"

    # Optional AI Keys / Local Ollama
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_ENDPOINT: str = "http://localhost:11434/v1"

    # Hugging Face Model Integration (Fine-tuned models)
    HF_API_TOKEN: Optional[str] = None
    HF_MODEL_ID: str = "veridion-legal-finetuned"
    HF_ENDPOINT_URL: Optional[str] = None

    # Paths
    CORPUS_DIR: str = "ml/corpus"
    DEPLOYMENTS_FILE: str = "backend/contracts/deployments.json"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    def load_deployments(self) -> None:
        """Loads deployed contract addresses from deployments.json if present."""
        import json
        import os
        if os.path.exists(self.DEPLOYMENTS_FILE):
            try:
                with open(self.DEPLOYMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.CASE_REGISTRY_ADDRESS = data.get("CaseRegistry", self.CASE_REGISTRY_ADDRESS)
                    self.AGENT_REGISTRY_ADDRESS = data.get("AgentRegistry", self.AGENT_REGISTRY_ADDRESS)
                    self.PREDICTION_MARKET_ADDRESS = data.get("PredictionMarket", self.PREDICTION_MARKET_ADDRESS)
                    self.EVIDENCE_BOUNTY_ADDRESS = data.get("EvidenceBounty", self.EVIDENCE_BOUNTY_ADDRESS)
                    self.REPUTATION_SETTLEMENT_ADDRESS = data.get("ReputationSettlement", self.REPUTATION_SETTLEMENT_ADDRESS)
            except Exception:
                pass


settings = Settings()
settings.load_deployments()

