import logging
import os
import types
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class BasePatch:
    def __init__(self):
        self._patched_functions = {}

    def _mark_as_patched(self, func: Callable, identifier: str):
        marker = f"__rlboost_patched_{identifier}__"
        setattr(func, marker, True)

    def _is_patched(self, func: Callable, identifier: str) -> bool:
        marker = f"__rlboost_patched_{identifier}__"
        return hasattr(func, marker)

    def apply(self) -> bool:
        raise NotImplementedError


class PatchManager:
    def __init__(self):
        self.patches: List[BasePatch] = []

    def register(self, patch: BasePatch):
        self.patches.append(patch)
        return self

    def apply_all(self) -> Dict[str, bool]:
        results = {}
        for patch in self.patches:
            patch_name = patch.__class__.__name__
            try:
                success = patch.apply()
                results[patch_name] = success
                if success:
                    logger.info(f"Successfully applied patch: {patch_name}")
                else:
                    logger.warning(f"Patch {patch_name} did not apply (may be already applied or not needed)")
            except Exception as e:
                logger.error(f"Failed to apply patch {patch_name}: {e}")
                results[patch_name] = False
        return results


def log_patch_results(results: Dict[str, bool]):
    successful = [name for name, success in results.items() if success]
    failed = [name for name, success in results.items() if not success]

    if successful:
        logger.info(f"Successfully applied patches: {', '.join(successful)}")
    if failed:
        logger.warning(f"Failed or skipped patches: {', '.join(failed)}")


def _env_enabled() -> bool:
    return os.getenv("ENABLE_RLBOOST_AUTOPATCH", "false").lower() in ("true", "1")


try:
    from wrapt.importer import when_imported

    @when_imported("sglang")
    def _patch_sglang(module: types.ModuleType) -> None:
        if not _env_enabled():
            logger.debug("Disabled by ENABLE_RLBOOST_AUTOPATCH")
            return

        from rlboost.sglang.patches import (
            ServerArgsPatch,
            IOStructPatch,
            TpWorkerPatch,
            SchedulerUpdateWeightsMixinPatch,
            SchedulerPatch,
            TokenizerCommunicatorMixinPatch,
            HttpServerPatch,
        )

        logger.info("Auto-applying rlboost patches to sglang...")

        manager = PatchManager()
        manager.register(ServerArgsPatch())
        manager.register(IOStructPatch())
        manager.register(TpWorkerPatch())
        manager.register(SchedulerUpdateWeightsMixinPatch())
        manager.register(SchedulerPatch())
        manager.register(TokenizerCommunicatorMixinPatch())
        manager.register(HttpServerPatch())

        results = manager.apply_all()
        log_patch_results(results)

except ImportError:
    logger.warning("wrapt not installed, autopatch disabled")


def apply_patches():
    from rlboost.sglang.patches import (
        ServerArgsPatch,
        IOStructPatch,
        TpWorkerPatch,
        SchedulerUpdateWeightsMixinPatch,
        SchedulerPatch,
        TokenizerCommunicatorMixinPatch,
        HttpServerPatch,
    )

    manager = PatchManager()
    manager.register(ServerArgsPatch())
    manager.register(IOStructPatch())
    manager.register(TpWorkerPatch())
    manager.register(SchedulerUpdateWeightsMixinPatch())
    manager.register(SchedulerPatch())
    manager.register(TokenizerCommunicatorMixinPatch())
    manager.register(HttpServerPatch())

    results = manager.apply_all()
    log_patch_results(results)

    return all(results.values())
