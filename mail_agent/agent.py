import logging

from .config import Config
from .llm import LLMClient
from .models import AgentAction, EmailDetail
from .proxy_client import ProxyClient

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, config: Config):
        self._config = config
        self._proxy = ProxyClient(
            base_url=config.proxy.base_url,
            api_key=config.proxy.api_key,
            timeout=config.proxy.timeout,
        )
        self._llm = LLMClient(
            model=config.llm.model,
            base_url=config.llm.base_url,
        )

    def run_once(self) -> int:
        """Fetch and process all unread emails. Returns the number processed."""
        folder = self._config.agent.folder
        folder_label = folder or "INBOX"

        logger.info("Fetching unread emails from '%s'...", folder_label)
        summaries = self._proxy.list_unread(folder=folder)

        if not summaries:
            logger.info("No unread emails in '%s'. Nothing to do.", folder_label)
            return 0

        logger.info("Found %d unread email(s) in '%s'.", len(summaries), folder_label)

        for summary in summaries:
            self._process_email(summary.uid, summary.subject, summary.sender, folder)

        logger.info("Finished. Processed %d email(s).", len(summaries))
        return len(summaries)

    # ------------------------------------------------------------------

    def _process_email(
        self, uid: int, subject: str, sender: str, folder: str | None
    ) -> None:
        logger.info(
            "Processing UID=%d | From: %s | Subject: %s",
            uid,
            sender,
            subject,
        )

        detail = self._proxy.get_email(uid, folder=folder)
        body = detail.body_text or detail.body_html
        date_str = detail.date.isoformat() if detail.date else "unknown"

        action = self._llm.decide_action(
            subject=detail.subject,
            sender=detail.sender,
            date=date_str,
            body=body,
            instructions=self._config.agent.instructions,
        )

        target_info = f" -> '{action.target_folder}'" if action.target_folder else ""
        logger.info(
            "LLM decision for UID=%d: action='%s'%s | Reason: %s",
            uid,
            action.action,
            target_info,
            action.reason or "-",
        )

        self._execute_action(uid, action, folder)

    def _execute_action(
        self, uid: int, action: AgentAction, folder: str | None
    ) -> None:
        act = action.action

        if act == "mark_read":
            logger.info("Marking UID=%d as read.", uid)
            self._proxy.mark_as_read(uid, folder=folder)
            logger.info("UID=%d marked as read. Done.", uid)

        elif act == "move":
            if not action.target_folder:
                logger.warning(
                    "Action 'move' for UID=%d has no target_folder — "
                    "falling back to mark_read.",
                    uid,
                )
                self._proxy.mark_as_read(uid, folder=folder)
                return
            logger.info("Moving UID=%d to folder '%s'.", uid, action.target_folder)
            self._proxy.move(uid, action.target_folder, folder=folder)
            logger.info("UID=%d moved to '%s'. Done.", uid, action.target_folder)

        elif act == "delete":
            logger.info("Deleting UID=%d (will land in Trash).", uid)
            self._proxy.delete(uid, folder=folder)
            logger.info("UID=%d deleted. Done.", uid)

        elif act == "keep":
            logger.info("Keeping UID=%d untouched (no action taken).", uid)

        elif act == "reply":
            logger.warning(
                "Action 'reply' for UID=%d is not yet implemented — "
                "falling back to mark_read.",
                uid,
            )
            self._proxy.mark_as_read(uid, folder=folder)

        else:
            logger.warning(
                "Unknown action '%s' for UID=%d — falling back to mark_read.",
                act,
                uid,
            )
            self._proxy.mark_as_read(uid, folder=folder)
