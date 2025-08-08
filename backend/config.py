from langchain.chat_models import init_chat_model
import os
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

log_dir = "logs/"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "app.log")

logger.add(
    log_path,
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time: YYYY-MM-DD} | {file}:{line} | {level} | {message}",
    encoding="utf-8",
)


config = {
    "openai":{
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "api_key": os.getenv("OPENAI_API_KEY")
    }
}


def initlization_llm(llm_type: str="openai"):
    try:
        logger.info(f"Initializing LLM of type: {llm_type}")
        llm_config = config[llm_type]
        llm = init_chat_model(
            model=llm_config["model"],
            model_provider=llm_type,
            temperature=llm_config["temperature"],
            api_key=llm_config["api_key"]
        )
        logger.info(f"LLM initialized successfully.")

        return llm
    except:
        logger.error(f"Failed to initialize LLM of type {llm_type}. Please check your configuration.")
        raise

llm = initlization_llm("openai")