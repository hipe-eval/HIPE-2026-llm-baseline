"""Local inference helpers for llama-cpp-python."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import platform
import time
from typing import Protocol


DEFAULT_MODEL_NAME = "mistralai/Ministral-3-3B-Instruct-2512"
LOGGER = logging.getLogger(__name__)


class PromptRunner(Protocol):
    def generate(self, prompt: str) -> "GenerationResult | str":
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
    n_gpu_layers: int | None = None
    flash_attn: bool = True


@dataclass(frozen=True)
class GenerationResult:
    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    elapsed_seconds: float
    input_tokens_per_second: float | None
    output_tokens_per_second: float | None


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


def auto_n_gpu_layers(*, supports_gpu_offload: bool) -> int:
    """Choose a sensible default for GPU offload.

    On Apple Silicon, prefer Metal offload when the runtime supports it.
    Otherwise default to CPU-only.
    """

    is_macos_arm = platform.system() == "Darwin" and platform.machine() == "arm64"
    return -1 if is_macos_arm and supports_gpu_offload else 0


def detect_gpu_backend(lib_dir: Path) -> str | None:
    names = {path.name.lower() for path in lib_dir.glob("*")}
    if any("metal" in name for name in names):
        return "metal"
    if any("cuda" in name or "cublas" in name for name in names):
        return "cuda"
    if any("vulkan" in name for name in names):
        return "vulkan"
    if any("hip" in name for name in names):
        return "hip"
    if any("sycl" in name for name in names):
        return "sycl"
    return None


def describe_runtime_backend(
    *,
    supports_gpu_offload: bool,
    n_gpu_layers: int,
    lib_dir: Path,
) -> str:
    if not supports_gpu_offload or n_gpu_layers == 0:
        return "cpu"
    return detect_gpu_backend(lib_dir) or "gpu-offload"


class LlamaCppRunner:
    """Thin wrapper around llama-cpp-python."""

    def __init__(self, model_path: str | Path, config: GenerationConfig) -> None:
        try:
            import llama_cpp
            from llama_cpp import Llama, llama_supports_gpu_offload
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is required for local inference"
            ) from exc

        supports_gpu_offload = llama_supports_gpu_offload()
        n_gpu_layers = config.n_gpu_layers
        if n_gpu_layers is None:
            n_gpu_layers = auto_n_gpu_layers(
                supports_gpu_offload=supports_gpu_offload
            )

        lib_dir = Path(llama_cpp.__file__).resolve().parent / "lib"
        backend = describe_runtime_backend(
            supports_gpu_offload=supports_gpu_offload,
            n_gpu_layers=n_gpu_layers,
            lib_dir=lib_dir,
        )

        self._config = GenerationConfig(
            temperature=config.temperature,
            seed=config.seed,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repeat_penalty,
            n_ctx=config.n_ctx,
            n_gpu_layers=n_gpu_layers,
            flash_attn=config.flash_attn,
        )
        LOGGER.info(
            "llama.cpp backend=%s n_gpu_layers=%s flash_attn=%s supports_gpu_offload=%s",
            backend,
            n_gpu_layers,
            config.flash_attn,
            supports_gpu_offload,
        )
        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=config.n_ctx,
            n_gpu_layers=n_gpu_layers,
            flash_attn=config.flash_attn,
            seed=config.seed,
            verbose=False,
        )

    def _format_prompt(self, prompt: str) -> str:
        # The prompt formatting is intentionally simple. If you want to adapt this
        # to another chat template or model family, this is the main place to edit.
        return f"[INST] {prompt.strip()} [/INST]"

    def _generate_formatted_prompt(self, formatted_prompt: str) -> GenerationResult:
        started_at = time.perf_counter()
        response = self._llm(
            formatted_prompt,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            top_k=self._config.top_k,
            repeat_penalty=self._config.repeat_penalty,
            stop=["</s>"],
        )
        elapsed_seconds = max(time.perf_counter() - started_at, 1e-9)
        prompt_tokens = None
        completion_tokens = None
        if isinstance(response, dict):
            usage = response.get("usage")
            if isinstance(usage, dict):
                raw_prompt_tokens = usage.get("prompt_tokens")
                if isinstance(raw_prompt_tokens, int):
                    prompt_tokens = raw_prompt_tokens
                raw_completion_tokens = usage.get("completion_tokens")
                if isinstance(raw_completion_tokens, int):
                    completion_tokens = raw_completion_tokens
        input_tokens_per_second = None
        if prompt_tokens is not None:
            input_tokens_per_second = prompt_tokens / elapsed_seconds
        output_tokens_per_second = None
        if completion_tokens is not None:
            output_tokens_per_second = completion_tokens / elapsed_seconds
        return GenerationResult(
            text=str(response["choices"][0]["text"]),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            elapsed_seconds=elapsed_seconds,
            input_tokens_per_second=input_tokens_per_second,
            output_tokens_per_second=output_tokens_per_second,
        )

    def generate(self, prompt: str) -> GenerationResult:
        return self._generate_formatted_prompt(self._format_prompt(prompt))
