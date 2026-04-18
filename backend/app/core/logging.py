import logging

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("endurasync").info(
        "starting app=%s env=%s version=%s",
        settings.app_name,
        settings.app_env,
        settings.app_version,
    )

