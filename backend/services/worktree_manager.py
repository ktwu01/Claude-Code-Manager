import asyncio
import logging
import os
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.worktree import Worktree as WorktreeModel

logger = logging.getLogger(__name__)

WORKTREE_DIR = ".claude-manager/worktrees"


@dataclass
class WorktreeInfo:
    path: str
    branch_name: str
    base_branch: str
    repo_path: str
    db_id: int | None = None


class WorktreeManager:
    def __init__(self, db_factory):
        self.db_factory = db_factory

    async def create(
        self,
        repo_path: str,
        branch_name: str,
        base_branch: str = "main",
        instance_id: int | None = None,
    ) -> WorktreeInfo:
        worktree_dir = os.path.join(repo_path, WORKTREE_DIR, branch_name)
        os.makedirs(os.path.dirname(worktree_dir), exist_ok=True)

        # Fetch latest from origin before creating worktree
        try:
            await self._git(repo_path, ["fetch", "origin"])
        except RuntimeError as e:
            logger.warning(f"git fetch origin failed (continuing with local): {e}")

        # Try to base on origin/<base_branch>, fallback to local branch
        start_point = f"origin/{base_branch}"
        try:
            await self._git(repo_path, ["rev-parse", "--verify", start_point])
        except RuntimeError:
            logger.warning(f"{start_point} not found, falling back to local {base_branch}")
            start_point = base_branch

        # Create worktree with a new branch
        await self._git(repo_path, ["worktree", "add", "-b", branch_name, worktree_dir, start_point])

        # Save to DB
        async with self.db_factory() as db:
            record = WorktreeModel(
                repo_path=repo_path,
                worktree_path=worktree_dir,
                branch_name=branch_name,
                base_branch=base_branch,
                instance_id=instance_id,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            db_id = record.id

        return WorktreeInfo(
            path=worktree_dir,
            branch_name=branch_name,
            base_branch=base_branch,
            repo_path=repo_path,
            db_id=db_id,
        )

    async def sync_latest(self, worktree_path: str, base_branch: str = "main") -> str:
        """Fetch origin and merge latest base branch into the worktree. Returns 'ok' or 'conflict'."""
        try:
            await self._git(worktree_path, ["fetch", "origin"])
        except RuntimeError as e:
            logger.warning(f"fetch failed during sync_latest: {e}")

        try:
            await self._git(worktree_path, ["merge", f"origin/{base_branch}",
                                             "-m", f"Merge origin/{base_branch} into working branch"])
            return "ok"
        except RuntimeError:
            # Abort the failed merge
            try:
                await self._git(worktree_path, ["merge", "--abort"])
            except RuntimeError:
                pass
            return "conflict"

    async def merge_to_main(
        self,
        worktree: WorktreeInfo,
        max_retries: int = 3,
        push: bool = True,
    ) -> str:
        """Rebase worktree branch onto origin/main, merge --ff-only, and push.

        Returns: 'merged', 'conflict', or 'push_failed'.
        """
        repo = worktree.repo_path
        base = worktree.base_branch

        for attempt in range(max_retries):
            try:
                # Fetch latest
                await self._git(repo, ["fetch", "origin"])

                # Rebase the task branch onto origin/<base>
                try:
                    await self._git(repo, ["rebase", f"origin/{base}", worktree.branch_name])
                except RuntimeError:
                    # Abort rebase on conflict
                    try:
                        await self._git(repo, ["rebase", "--abort"])
                    except RuntimeError:
                        pass
                    return "conflict"

                # Checkout base branch and reset to origin
                await self._git(repo, ["checkout", base])
                await self._git(repo, ["reset", "--hard", f"origin/{base}"])

                # Fast-forward merge
                await self._git(repo, ["merge", "--ff-only", worktree.branch_name])

                # Push
                if push:
                    try:
                        await self._git(repo, ["push", "origin", base])
                    except RuntimeError as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Push rejected (attempt {attempt + 1}), retrying: {e}")
                            # Reset and retry
                            await self._git(repo, ["reset", "--hard", f"origin/{base}"])
                            continue
                        else:
                            return "push_failed"

                # Update DB status
                if worktree.db_id:
                    async with self.db_factory() as db:
                        await db.execute(
                            update(WorktreeModel)
                            .where(WorktreeModel.id == worktree.db_id)
                            .values(status="merged")
                        )
                        await db.commit()

                return "merged"

            except RuntimeError as e:
                logger.error(f"merge_to_main error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
                return "conflict"

        return "conflict"

    async def merge(self, worktree: WorktreeInfo) -> str:
        """Merge worktree branch back (legacy, no-ff). Returns 'merged' or 'conflict'."""
        repo = worktree.repo_path
        await self._git(repo, ["checkout", worktree.base_branch])

        try:
            await self._git(repo, [
                "merge", "--no-ff", worktree.branch_name,
                "-m", f"Merge branch '{worktree.branch_name}'",
            ])
            status = "merged"
        except RuntimeError:
            await self._git(repo, ["merge", "--abort"])
            status = "conflict"

        if worktree.db_id:
            async with self.db_factory() as db:
                await db.execute(
                    update(WorktreeModel)
                    .where(WorktreeModel.id == worktree.db_id)
                    .values(status=status)
                )
                await db.commit()

        return status

    async def remove(self, worktree: WorktreeInfo) -> None:
        try:
            await self._git(worktree.repo_path, ["worktree", "remove", "--force", worktree.path])
        except RuntimeError:
            pass
        try:
            await self._git(worktree.repo_path, ["branch", "-D", worktree.branch_name])
        except RuntimeError:
            pass

        if worktree.db_id:
            async with self.db_factory() as db:
                await db.execute(
                    update(WorktreeModel)
                    .where(WorktreeModel.id == worktree.db_id)
                    .values(status="removed", removed_at=datetime.utcnow())
                )
                await db.commit()

    async def _git(self, cwd: str, args: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {stderr.decode()}")
        return stdout.decode().strip()
