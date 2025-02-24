import tempfile
import webbrowser
import os
import shutil

from zoo.core.util import zlogging
from zoo.core.commands import action
from zoo.core.util import processes

logger = zlogging.getLogger(__name__)

_API_DOC_COMMAND = "sphinx-apidoc -f --implicit-namespaces -o {outputFolder} {sourceCodeFolder} -M"
# the packages.rst file octree which we write out to the packages.rst
_OCTREE_HEADER = """
.. toctree::
   :maxdepth: 2
   
   {packages}
"""
# The relative location where each packages source rst files will be copied too.
PACKAGE_RELATIVE_OUTPUT_PATH = "packages/{packageName}"
# the packages rst file which we write each package index file too.
PACKAGES_HEADER_PATH = "packages/packages.rst"


class GenerateDocs(action.Action):
    """This Command generates API documentation using sphinx.

    Before Building the documentation you'll first need to pip install the following libraries:

        sphinx
        sphinx_rtd_theme

    Please see the how to Build documentation to see how to custom package level configuration.

    """
    id = "generateDocs"

    def arguments(self, argParser):

        argParser.add_argument("--packages",
                               required=True,
                               help="a list of package names to generate documentation for, if '*' is specified"
                                    "then all packages within the config will be generated",
                               type=str,
                               nargs="+")

        argParser.add_argument("--apiDocs",
                               help="If Set the API will generate rst docs either 'sphinx-apidoc'",
                               action="store_true")
        argParser.add_argument("--apiDocsOutputName",
                               help="The output directory base name for the api docs",
                               type=str)
        argParser.add_argument("--build",
                               help="If set the Html documentation for the given packages will be "
                                    "generated into core/docs/build",
                               action="store_true")
        argParser.add_argument("--keepSource",
                               help="if set then the folder which contain all sources directories will not be "
                                    "deleted after generation",
                               action="store_true")
        argParser.add_argument("--launch",
                               help="Launches the users default webbrowser with the new html doc, only valid "
                                    "when building the html",
                               action="store_true")

    def run(self):
        # if the command is launched without an environment set we first set that up using defaults.
        # ignore build commands here as it could lead to errors
        if not self.config.resolver.cache:
            self.config.resolver.resolveFromPath(self.config.resolver.environmentPath(), apply=True,
                                                 runCommandScripts=False
                                                 )
        if not self.options.build and not self.options.apiDocs and self.options.launch:
            self._launchWebBrowser()
            return
        # steps
        currentPackages = {i.name: i for i in self.config.resolver.cache.values()}
        requestedPackages = self.options.packages or []

        packagesForGeneration = {}
        logger.debug("Filtering requested packages")
        #   grab all current packages in environment and only grab the specified
        for request in requestedPackages:
            if request == "*":
                packagesForGeneration = currentPackages
                break
            matchedPkg = currentPackages.get(request)
            if matchedPkg is None:
                logger.warning("Missing package by the name: {}".format(request))
                continue
            packagesForGeneration[str(matchedPkg)] = matchedPkg

        logger.debug("Valid packages are: {}".format(list(packagesForGeneration.keys())))

        #   check and get all package documentation source folders paths
        validPackages = {}
        logger.debug("Gathering valid packages with documentation")

        for packageName, package in packagesForGeneration.items():
            docInfo = package.documentation
            if not docInfo:
                logger.warning("Missing Documentation for package: {}".format(packageName))
                continue
            # resolve package level paths ie. "{self}"
            package.resolveEnvPath("docSourceFolder", [docInfo["sourceFolder"]],
                                   applyEnvironment=False)
            sourceFolder = package.resolvedEnv["docSourceFolder"].values[0]

            masterDoc = docInfo.get("masterDoc", "index")
            package.resolveEnvPath("docsSourceCodeFolder", [docInfo["sourceCodeFolder"]],
                                   applyEnvironment=False)

            sourceCode = package.resolvedEnv["docsSourceCodeFolder"].values[0]
            if not os.path.exists(sourceFolder):
                logger.error("Unable to find sourceFolder for package: {}".format(packageName))
                continue
            masterFile = os.path.join(sourceFolder, masterDoc)
            if not os.path.exists(masterFile):
                logger.error("Unable to find master file for package: {}".format(packageName))
                continue
            if not os.path.exists(sourceCode):
                logger.error("Unable to find source Code for package: {}".format(packageName))
                continue

            validPackages[str(packageName)] = {
                "package": package,
                "source": sourceFolder,
                "code": sourceCode,
                "masterPath": "/".join((package.name, masterDoc))
            }

        # at this point the packages have been validated and ready to start running generator commands
        # if api-docs is set then just run the api-doc command
        if self.options.apiDocs:
            self.generateApiDocs(validPackages)

        if self.options.build:
            #   create temp local folder
            outputRoot = tempfile.mkdtemp()
            logger.debug("Temporary output path for source files: {}".format(outputRoot))
            try:
                self.generateDocs(outputRoot, validPackages)
                self._launchWebBrowser()
            finally:
                # remove the now redundant merged source directories
                if not self.options.keepSource:
                    shutil.rmtree(outputRoot)

    def generateApiDocs(self, packages):
        outputFolderName = self.options.apiDocsOutputName
        for packageName, info in packages.items():
            sourceFolder = info["source"]
            if outputFolderName is not None:
                sourceFolder = os.path.join(sourceFolder, outputFolderName)
            cmd = _API_DOC_COMMAND.format(outputFolder=sourceFolder,
                                          sourceCodeFolder=info["code"])
            logger.debug("Generating Api documentation for pkg: {}".format(packageName))
            output = processes.checkOutput(cmd)
            print(output[0].decode("ascii"))

    def generateDocs(self, outputRoot, packages):
        from sphinx.cmd import build as sphinxbuild
        outputSource = os.path.join(outputRoot, "source")
        primarySource = os.path.join(self.config.corePath, "docs", "source")
        logger.info("Output folder: {}".format(outputSource))
        #   copy zootools primary docs source folder to temp/source
        logger.debug("Copying primary source files: {}".format(primarySource))
        shutil.copytree(primarySource,
                        outputSource)
        # copy over the changelon.md file
        shutil.copyfile(os.path.join(self.config.corePath, "CHANGELOG.md"),
                        os.path.join(outputSource, "CHANGELOG.md"))

        #   copy all matching package documentation sources into temp/source/packages/{package_name}
        docReferences = []
        buildFolder = os.path.join(self.config.corePath, "docs", "build")
        for pkgName, info in packages.items():
            sourceFolder = info["source"]
            output = os.path.join(outputSource,
                                  PACKAGE_RELATIVE_OUTPUT_PATH.format(packageName=info["package"].name))
            logger.debug("Copying package '{}' source documentation to :{}".format(pkgName, output))
            shutil.copytree(sourceFolder,
                            output)
            # now copy the changelog file to the packages new source folder location if any
            changelog = os.path.join(info["package"].root, "CHANGELOG.md")
            if os.path.exists(changelog):
                shutil.copyfile(changelog, os.path.join(output, "CHANGELOG.md"))
            docReferences.append(info["masterPath"])

        #   update the package.rst file to contain the octree with all packages
        packagesrst = os.path.join(outputSource, PACKAGES_HEADER_PATH)
        logger.debug("Updating package.rst references")
        with open(packagesrst, "a") as f:
            f.write(_OCTREE_HEADER.format(packages="\n   ".join(docReferences)))

        #   run doc gen
        logger.debug("Running sphinx build")
        sphinxbuild.make_main(['-M', 'html', outputSource, buildFolder])

        logger.debug("Completed build sphinx documentation.")

    def _launchWebBrowser(self):
        buildFolder = os.path.join(self.config.corePath, "docs", "build")
        indexFile = os.path.join(buildFolder, "html/index.html").replace("\\", "/")
        if self.options.launch and os.path.exists(indexFile):
            logger.debug("Launching webbrowser for index.html")
            webbrowser.open(indexFile)
