# chatserver/chat/management/commands/test.py

import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test command for GitHub Actions"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("========== CI/CD TEST START =========="))

        logger.info("CI/CD Test: Logger initialized.")

        for i in range(1, 6):
            msg = f"Running step {i}/5..."
            self.stdout.write(msg)
            logger.info(msg)
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS("All steps completed successfully."))
        logger.info("CI/CD Test finished successfully.")

        self.stdout.write(self.style.SUCCESS("========== CI/CD TEST END =========="))