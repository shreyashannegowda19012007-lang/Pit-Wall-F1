"""
Background Async Job Queue Manager.
Manages long-running asynchronous operations (100k Monte Carlo runs, full race backtests, system evaluation benchmarks).
Supports job creation, status polling (/api/v1/jobs/{job_id}), and persistent result storage.
"""

from typing import Dict, List, Optional, Any, Callable
import threading
import datetime
import uuid
import json

from database_migrations import db_manager
from logger import logger


class JobQueueManager:
    """
    In-memory & SQLite-backed asynchronous background job execution manager.
    """

    @classmethod
    def create_job(cls, job_type: str) -> str:
        """Enqueues a new background job and returns job_id."""
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO background_jobs (job_id, job_type, status, progress_pct, created_at, updated_at)
                VALUES (?, ?, 'QUEUED', 0.0, ?, ?)
            """, (job_id, job_type, now_str, now_str))
            conn.commit()
        return job_id

    @classmethod
    def execute_async_job(cls, job_id: str, target_func: Callable, *args, **kwargs):
        """Launches target_func in a daemon thread, updating job status upon completion or error."""
        def worker():
            try:
                cls._update_status(job_id, "RUNNING", progress_pct=10.0)
                res = target_func(*args, **kwargs)
                res_json = json.dumps(res) if isinstance(res, (dict, list)) else str(res)
                cls._update_status(job_id, "COMPLETE", progress_pct=100.0, result_json=res_json)
            except Exception as e:
                logger.error(f"Job {job_id} failed: {str(e)}")
                cls._update_status(job_id, "FAILED", error_message=str(e))

        thread = threading.Thread(target=worker, daemon=False)
        thread.start()

        if not hasattr(cls, '_active_threads'):
            cls._active_threads = []

            import atexit
            def wait_all_jobs():
                for t in cls._active_threads:
                    if t.is_alive():
                        t.join()
            atexit.register(wait_all_jobs)

        cls._active_threads.append(thread)

    @classmethod
    def get_job_status(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves current job status and results."""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM background_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None

            result = json.loads(row["result_json"]) if row["result_json"] else None
            return {
                "job_id": row["job_id"],
                "job_type": row["job_type"],
                "status": row["status"],
                "progress_pct": row["progress_pct"],
                "result": result,
                "error_message": row["error_message"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    @classmethod
    def _update_status(cls, job_id: str, status: str, progress_pct: float = 0.0, result_json: Optional[str] = None, error_message: Optional[str] = None):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE background_jobs
                SET status = ?, progress_pct = ?, result_json = COALESCE(?, result_json), error_message = ?, updated_at = ?
                WHERE job_id = ?
            """, (status, progress_pct, result_json, error_message, now_str, job_id))
            conn.commit()
