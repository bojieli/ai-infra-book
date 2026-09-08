import logging
import os
import sys

logger = logging.getLogger(__name__)

def launch_server(server_args, *args, **kwargs):
    """
    Wrapper around sglang.srt.entrypoints.http_server.launch_server
    that applies RLBoost patches before launching.
    """
    os.environ["ENABLE_RLBOOST_AUTOPATCH"] = "true"
    from rlboost.sglang.autopatch import apply_patches
    apply_patches()

    logger.info("Launching SGLang server with RLBoost patches...")
    from sglang.srt.entrypoints.http_server import launch_server as original_launch_server
    
    return original_launch_server(server_args, *args, **kwargs)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Apply patches early to support extra CLI arguments in prepare_server_args
    os.environ["ENABLE_RLBOOST_AUTOPATCH"] = "true"
    from rlboost.sglang.autopatch import apply_patches
    apply_patches()

    logger.info("Launching SGLang server...")
    from sglang.srt.server_args import prepare_server_args
    from sglang.srt.utils import kill_process_tree

    server_args = prepare_server_args(sys.argv[1:])

    try:
        # We can call our wrapper launch_server, or the original one since patches are already applied.
        # Using the wrapper ensures consistency.
        launch_server(server_args)
    finally:
        kill_process_tree(os.getpid(), include_parent=False)


if __name__ == "__main__":
    main()