import logging
import time

from django.conf import settings
from django.core.cache import cache

from api.services.ai_prompt_service import AIPromptService
from api.services.ai_service import (
    AIClient,
    AIServiceError,
    read_int_setting,
)

logger = logging.getLogger(__name__)


class AIInsightsService:


    BUDGET_KEY = "ai-summary-calls"

    @classmethod
    def reserve_call(cls):
  
        limit = read_int_setting("AI_MAX_CALLS_PER_HOUR", 60, 0, 100000)

        if limit == 0:
            return False

        hour = time.strftime("%Y%m%d%H", time.gmtime())
        key = f"{cls.BUDGET_KEY}:{hour}"

        try:
            cache.add(key, 0, 3700)
            count = cache.incr(key)
        except Exception:
            # Without a working counter the budget cannot be enforced, so
            # the safe choice is to not spend money.
            logger.warning("The AI call budget could not be checked.")
            return False

        return count <= limit

    @classmethod
    def generate(
        cls,
        github_repository,
        category,
        technologies,
        analysis_scores,
        evaluation=None,
    ):
        if not AIClient.is_enabled():
            return None

        if not cls.reserve_call():
            logger.info("The AI summary budget for this hour is spent.")
            return None

        try:
            message = AIPromptService.build_user_message(
                github_repository,
                category,
                technologies,
                analysis_scores,
                evaluation,
            )
            result = AIClient.complete(
                AIPromptService.system_prompt(
                    cls.language(),
                ),
                message,
            )
            summary = AIPromptService.validate_output(
                result["text"],
                truncated=result["truncated"],
            )

        except AIServiceError as error:
            logger.warning("AI summary failed: %s", error)
            return None

        except Exception:
            logger.exception("Unexpected error while building the AI summary.")
            return None

        if summary is None:
            logger.warning("The AI summary was rejected by validation.")

        return summary

    @staticmethod
    def language():
        """Language of the summary (AI_SUMMARY_LANGUAGE), or None."""
        return getattr(settings, "AI_SUMMARY_LANGUAGE", None)
