from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "enterprise_docs"

    # Ingestion
    chunk_size: int = 512
    chunk_overlap: int = 64
    data_dir: str = "./data/sample_docs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
