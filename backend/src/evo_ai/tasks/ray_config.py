"""Ray cluster configuration and initialization."""

import os
from typing import Optional

import ray
import structlog

logger = structlog.get_logger(__name__)


def init_ray(
    address: Optional[str] = None,
    num_cpus: Optional[int] = None,
    num_gpus: Optional[int] = None,
    dashboard_host: str = "0.0.0.0",
    dashboard_port: int = 8265,
) -> None:
    """
    Initialize Ray cluster.

    Args:
        address: Ray cluster address (None for local, "auto" for auto-discovery)
        num_cpus: Number of CPUs to use (None for all available)
        num_gpus: Number of GPUs to use (None for all available)
        dashboard_host: Dashboard host address
        dashboard_port: Dashboard port

    Examples:
        # Local mode (single machine)
        init_ray()

        # Connect to existing cluster
        init_ray(address="ray://localhost:10001")

        # Auto-discover cluster
        init_ray(address="auto")

        # Local with resource limits
        init_ray(num_cpus=4, num_gpus=1)
    """
    if ray.is_initialized():
        logger.warning("ray_already_initialized")
        return

    # Get configuration from environment
    ray_address = address or os.getenv("RAY_ADDRESS")

    logger.info(
        "initializing_ray",
        address=ray_address,
        num_cpus=num_cpus,
        num_gpus=num_gpus
    )

    try:
        if ray_address:
            # Connect to existing cluster
            ray.init(
                address=ray_address,
                dashboard_host=dashboard_host,
                dashboard_port=dashboard_port,
                logging_level="INFO",
                namespace="evo_ai",
            )
        else:
            # Start local cluster
            ray.init(
                num_cpus=num_cpus,
                num_gpus=num_gpus,
                dashboard_host=dashboard_host,
                dashboard_port=dashboard_port,
                logging_level="INFO",
                namespace="evo_ai",
                _temp_dir="/tmp/ray",  # Explicit temp dir
            )

        logger.info(
            "ray_initialized",
            nodes=len(ray.nodes()),
            resources=ray.available_resources()
        )

    except Exception as e:
        logger.error("ray_initialization_failed", error=str(e))
        raise


def shutdown_ray() -> None:
    """Shutdown Ray cluster."""
    if not ray.is_initialized():
        logger.warning("ray_not_initialized")
        return

    logger.info("shutting_down_ray")

    try:
        ray.shutdown()
        logger.info("ray_shutdown_complete")
    except Exception as e:
        logger.error("ray_shutdown_failed", error=str(e))


def get_cluster_info() -> dict:
    """
    Get Ray cluster information.

    Returns:
        Dictionary with cluster details
    """
    if not ray.is_initialized():
        return {
            "initialized": False,
            "error": "Ray not initialized"
        }

    return {
        "initialized": True,
        "nodes": len(ray.nodes()),
        "available_resources": ray.available_resources(),
        "cluster_resources": ray.cluster_resources(),
    }
