"""Model download and management utilities."""

from pathlib import Path
from typing import Callable, Optional

from huggingface_hub import snapshot_download
from huggingface_hub.constants import HF_HUB_CACHE

from ..config.settings import WhisperModel


class ModelManager:
    """Manages Whisper model downloads and availability."""

    @staticmethod
    def get_hf_repo(model: WhisperModel) -> str:
        """Get the HuggingFace repository name for a model."""
        return model.hf_repo

    @staticmethod
    def _get_cache_dir(model: WhisperModel) -> Path:
        """Get the cache directory for a model."""
        repo_id = model.hf_repo
        # HuggingFace cache format: models--{org}--{repo}
        repo_dir_name = f"models--{repo_id.replace('/', '--')}"
        return Path(HF_HUB_CACHE) / repo_dir_name

    @staticmethod
    def is_model_downloaded(model: WhisperModel) -> bool:
        """
        Check if a model is already downloaded in the HuggingFace cache.

        Args:
            model: The WhisperModel to check

        Returns:
            True if model is fully downloaded, False otherwise
        """
        repo_id = model.hf_repo
        if not repo_id:
            return False

        # Check if cache directory exists with snapshots
        cache_dir = ModelManager._get_cache_dir(model)
        snapshots_dir = cache_dir / "snapshots"

        if not snapshots_dir.exists():
            return False

        # Check if there's at least one snapshot with files
        try:
            for snapshot in snapshots_dir.iterdir():
                if snapshot.is_dir() and any(snapshot.iterdir()):
                    return True
        except (OSError, PermissionError):
            pass

        return False

    @staticmethod
    def download_model(
        model: WhisperModel,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Download a model from HuggingFace.

        Args:
            model: The WhisperModel to download
            progress_callback: Optional callback for progress updates (receives status text)

        Returns:
            True if download successful, False otherwise

        Raises:
            Exception: If download fails
        """
        repo_id = model.hf_repo
        if not repo_id:
            raise ValueError(f"No HuggingFace repo defined for model {model.value}")

        if progress_callback:
            progress_callback(f"Downloading {model.display_name}...")

        try:
            # Download the model snapshot
            snapshot_download(
                repo_id=repo_id,
                local_files_only=False,
            )

            if progress_callback:
                progress_callback(f"{model.display_name} download complete")

            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"Download failed: {str(e)}")
            raise

    @staticmethod
    def get_downloaded_models() -> list[WhisperModel]:
        """
        Get a list of all downloaded models.

        Returns:
            List of WhisperModel enums that are available locally
        """
        downloaded = []
        for model in WhisperModel:
            if ModelManager.is_model_downloaded(model):
                downloaded.append(model)
        return downloaded

    @staticmethod
    def get_model_size_mb(model: WhisperModel) -> int:
        """
        Get the approximate download size of a model in MB.

        Args:
            model: The WhisperModel to check

        Returns:
            Size in MB
        """
        return model.size_mb
