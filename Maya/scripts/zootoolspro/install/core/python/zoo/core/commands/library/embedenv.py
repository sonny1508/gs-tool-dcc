from zoo.core.util import zlogging
from zoo.core.commands import action

logger = zlogging.getLogger(__name__)


class EmbedEnv(action.Action):
    """Loads and embed current environment into the current process
    """
    id = "env"

    def arguments(self, argParser):
        argParser.add_argument("--apply",
                               action="store_true",
                               help="")
        # todo: support specifying packages
        # argParser.add_argument(
        #     "packages", type=list, nargs='*',
        #     help='packages to use in the target environment')

    def run(self):
        apply = self.options.apply
        from zoo.core.util import env
        env.addToEnv("PYTHONPATH", [self.config.pythonPath])
        self.config.resolver.resolveFromPath(self.config.resolver.environmentPath(), apply=apply)
        return True

