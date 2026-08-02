"""
Celery tasks — async bridges that call LangGraph workflows.
"""
import structlog
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, name="run_daily_content_workflow", max_retries=3)
def run_daily_content_workflow(self, job_id: str):
    """
    Entry point for the daily content pipeline.
    Research → Script → Review → Voice → Video → Thumbnail → Publish
    """
    logger.info("workflow.started", job_id=job_id, workflow="daily_content")
    try:
        # TODO: import and invoke LangGraph workflow
        # from workflows.daily_content import run_workflow
        # run_workflow(job_id)
        logger.info("workflow.completed", job_id=job_id)
    except Exception as exc:
        logger.error("workflow.failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="run_breaking_news_workflow", max_retries=2)
def run_breaking_news_workflow(self, job_id: str):
    logger.info("workflow.started", job_id=job_id, workflow="breaking_news")
    try:
        pass  # TODO
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="run_weekly_review_workflow", max_retries=1)
def run_weekly_review_workflow(self, job_id: str):
    logger.info("workflow.started", job_id=job_id, workflow="weekly_review")
    try:
        pass  # TODO
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
