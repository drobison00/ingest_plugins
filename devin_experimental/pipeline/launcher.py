"""Pipeline launching utilities."""

from nv_ingest.framework.orchestration.ray.util.pipeline.pipeline_runners import run_pipeline
from nv_ingest.pipeline.config.loaders import load_pipeline_config


def launch_pipeline(pipeline_config_path: str):
    """
    Launch a pipeline from a config file.

    Parameters
    ----------
    pipeline_config_path : str
        Path to the pipeline YAML config file.

    Returns
    -------
    interface
        The pipeline interface object.
    """
    pipeline_config = load_pipeline_config(pipeline_config_path)
    interface = run_pipeline(
        pipeline_config=pipeline_config,
        block=False,
        run_in_subprocess=False,
        disable_dynamic_scaling=True,
        libmode=False,
        quiet=False,
    )
    return interface


def get_stage_actor(interface, stage_name: str):
    """
    Get the actor for a specific pipeline stage.

    Parameters
    ----------
    interface
        The pipeline interface object.
    stage_name : str
        Name of the stage to get the actor for.

    Returns
    -------
    ray.actor.ActorHandle
        The actor handle for the stage.

    Raises
    ------
    RuntimeError
        If no actor is found or multiple actors exist for the stage.
    """
    pipeline = interface._pipeline
    actors_by_stage = pipeline.topology.get_stage_actors()
    actors = actors_by_stage.get(stage_name) or []
    if not actors:
        raise RuntimeError(f"No actors found for stage '{stage_name}'. Available: {list(actors_by_stage.keys())}")
    if len(actors) != 1:
        raise RuntimeError(f"Expected exactly 1 actor for '{stage_name}', found {len(actors)}.")
    return actors[0]
