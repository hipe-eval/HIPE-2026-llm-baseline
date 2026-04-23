"""Local inference helpers for llama-cpp-python."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


DEFAULT_MODEL_NAME = "mistralai/Ministral-3-3B-Instruct-2512"


class PromptRunner(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate a raw response for a prompt."""


@dataclass(frozen=True)
class GenerationConfig:
    # Keep decoding settings in one small object so participants can change them
    # without digging through the inference call.
    temperature: float = 0.0
    seed: int = 42
    max_tokens: int = 256
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.0
    n_ctx: int = 8192
    n_gpu_layers: int = 0


def resolve_model_path(
    *,
    model_path: str | None,
    hf_repo: str | None = None,
    hf_filename: str | None = None,
    cache_dir: str | None = None,
) -> Path:
    if model_path:
        path = Path(model_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Model file does not exist: {path}")
        return path

    if not (hf_repo and hf_filename):
        raise ValueError(
            "Provide --model-path or both --hf-repo and --hf-filename for a GGUF file"
        )

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface-hub is required to resolve model files from Hugging Face"
        ) from exc

    downloaded = hf_hub_download(
        repo_id=hf_repo,
        filename=hf_filename,
        cache_dir=cache_dir,
    )
    return Path(downloaded).resolve()


class LlamaCppRunner:
    """Thin wrapper around llama-cpp-python."""

    def __init__(self, model_path: str | Path, config: GenerationConfig) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is required for local inference"
            ) from exc

        self._config = config
        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
            seed=config.seed,
            verbose=False,
        )

    def generate(self, prompt: str) -> str:
        # The prompt formatting is intentionally simple. If you want to adapt this
        # to another chat template or model family, this is the main place to edit.
        formatted_prompt = f"<s>[INST] {prompt.strip()} [/INST]"
        response = self._llm(
            formatted_prompt,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            top_k=self._config.top_k,
            repeat_penalty=self._config.repeat_penalty,
            stop=["</s>"],
        )
        return str(response["choices"][0]["text"])
