"""Contains all the global constants that zoo tools references, this values should never
be modified at runtime.
"""

#: Environment variable that sets the location of the config folder
ZOO_CFG_PATH_ENV = "ZOO_CONFIG_PATH"
#: Environment variable that sets the installed packages location.
ZOO_PKG_PATH_ENV = "ZOO_PACKAGES_PATH"
#: package environment json environment variable
ZOO_PKG_VERSION_PATH = "ZOO_PACKAGE_VERSION_PATH"
#: basename for the package configuration file
ZOO_PACKAGE_VERSION_FILE = "ZOO_PACKAGE_VERSION_FILE"
#: cache folder for all zootools temp folders.
CACHE_FOLDER_PATH_ENV = "ZOO_CACHE_FOLDER_PATH"
#: Config folder name.
CONFIG_FOLDER_NAME = "config"
#: Packages folder name.
PKG_FOLDER_NAME = "packages"
#: Environment variable which defines the location of CLI commands.
COMMANDLIBRARY_ENV = "ZOO_CMD_PATH"
#: environment key which defines the location for all descriptor types
ZOO_DESCRIPTOR_PATH = "ZOO_DESCRIPTOR_PATH"
#: file names to exclude when installing/copying packages
FILE_FILTER_EXCLUDE = (".gitignore", ".gitmodules", ".flake8.ini",
                       ".hound.yml", "setup.py", "*.git", "*.vscode", "*__pycache__",
                       "*.idea", "MANIFEST.ini", "*.pyc", "*.gitlab-ci.yml")
#: config token which can be used in descriptor paths
#: this will be converted to the abspath
CONFIG_FOLDER_TOKEN = "{config}"
#: package folder token for descriptors
#: resolves to each package root
PKG_FOLDER_TOKEN = "{self}"
INSTALL_FOLDER_TOKEN = "{install}"
#: per package file name
PACKAGE_NAME = "zoo_package.json"
DEPENDENT_FILTER = r"\{(.*?)\}"
#: The CLI root argument parser name
CLI_ROOT_NAME = "Zootools CLI"
#: the environment variable for ZOO_ADMIN flag
ZOO_ADMIN = "ZOO_ADMIN"
#: default preferences path which will be add to the preference_roots.config on build
DEFAULT_PREFS_PATH = "~/zoo_preferences"
