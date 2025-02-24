from zoo.core.util import zlogging

from zoo.core.commands import action


logger = zlogging.getLogger(__name__)


class UninstallPackage(action.Action):
    id = "uninstallPackage"

    def arguments(self, argParser):
        argParser.add_argument("--name",
                               required=True,
                               type=str)
        argParser.add_argument("--remove",
                               action="store_true")

    def run(self):
        logger.debug("Running uninstall command for package: {}".format(self.options.name))
        descriptor = self.config.descriptorForPackageName(self.options.name)
        if not descriptor:
            logger.error("No package by the name: {}".format(self.options.name))
            return
        try:
            descriptor.resolve()
        except ValueError:
            logger.error("Failed to resolve descriptor: {}".format(self.options.name),
                         exc_info=True, extra=self.options.name)
            return
        descriptor.uninstall(self.options.remove)
