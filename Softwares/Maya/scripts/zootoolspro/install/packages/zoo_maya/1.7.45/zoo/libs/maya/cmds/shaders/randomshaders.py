"""Module for assigning and managing randomized shaders

Author: Andrew Silke
"""
import random

from maya import cmds

from zoovendor.six.moves import range

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.utils import color as colorutils

from zoo.libs.maya.cmds.shaders import shadermulti, shaderutils
from zoo.libs.maya.cmds.objutils import namehandling


def split(lst, n):
    """Divide a list into a list of multiple lists

    https://stackoverflow.com/questions/2130016/splitting-a-list-into-n-parts-of-approximately-equal-length

    :param lst: any python list
    :type lst: list()
    :param n: The number of lists to create
    :type n: int
    :return listsInList: returns a list of lists, the list is now split into n lists.
    :rtype listsInList: list(list)
    """
    k, m = divmod(len(lst), n)
    return list(lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def indexInList(lst, index):
    """Simple function that returns True False if an index is in a list

    :param lst: any python list
    :type lst: list()
    :param index: the index number of a list
    :type index: int
    :return isInList: True if the index is in a list, False if not.
    :rtype isInList: bool
    """
    return index < len(lst)


class RandomShader(object):
    """Class for assigning random colors to an object selection, maybe shells in the future
    """

    def __init__(self):
        """Class for assigning random colors to an object selection, maybe shells in the future

        Code example:

            from zoo.libs.maya.cmds.shaders import randomshaders
            inst = randomshaders.RandomShader()

            inst.setObjs(objList)
            inst.setShaderAmount(5)
            inst.setValueRange(0.1, 0.3)
            inst.setHueRange(10.0, 45.0)
            inst.setSaturationRange(0.5, 0.6)
            inst.setAffectShells(False)
            inst.setShaderBaseName("someName")  # triggers a rename if live
            inst.setSuffix(True)
            inst.reseedColors()
            inst.reseedAssignments()
            inst.setRenderer()

            inst.randomize()  # randomizes shader assignments based off new shaders.

            inst.clearCache()

        """
        self.objList = list()
        self.nodeList = list()
        self.shaderInstances = list()
        self.nodeShaderList = list(list())  # Eg. objects who belong to the first shader self.objShaderList[0]
        self.colMultipliers = list()
        self.color = [0.5, 0.5, 0.0]
        self.shaderAmount = 3
        self.valueRange = [0.0 - 1.0]
        self.valueRangeFloat = 1.0
        self.valueVal = 0.5
        self.saturationRange = [0.0 - 1.0]
        self.saturationRangeFloat = 1.0
        self.saturationRangeMid = 0.5
        self.saturationVal = 0.5
        self.hueRange = [0.0 - 360.0]
        self.hueRangeFloat = 360.0
        self.hueVal = 180.0
        self.affectShells = False
        self.shaderBaseName = ""
        self.shaderType = ""
        self.renderer = ""
        self.suffix = False
        self.lockHsvColor = [180.0, 0.5, 0.5]
        self.specularColor = [0.0, 0.0, 0.0]
        self.shadersWereSelected = False
        self.knownShaders = True
        self.useShadersBool = False

    # ----------------
    # Setters
    # ----------------

    def setObjs(self, objList):
        """Adds the objects to the class as a zapi node list self.nodeList

        :param objList: A list of object names
        :type objList: list(str)
        """
        self.objList = objList
        self.nodeList = list(zapi.nodesByNames(objList))
        self._randomizeObjects()

    def setSelectedObjs(self):
        selObjs = cmds.ls(selection=True, long=True)
        if not selObjs:
            output.displayWarning("No objects are selected, please select objects for the shader assignment.")
            return list()
        self.setObjs(list(selObjs))
        return selObjs

    def setShaderAmount(self, shaderAmount):
        self.shaderAmount = shaderAmount

    def setColor(self, color):
        self.color = color

    def setValueRangeColor(self, color, valueRangeFloat):
        self.valueVal = colorutils.convertRgbToHsv(color)[2]
        valueRange = [self.valueVal - (valueRangeFloat / 2), self.valueVal + (valueRangeFloat / 2)]
        valueRange = self._colorRangeClamp(valueRange)
        self.valueRange = valueRange
        self.valueRangeFloat = valueRangeFloat
        self.setColor(color)  # Updates color too

    def setSaturationRangeColor(self, color, saturationRangeFloat):
        self.saturationVal = colorutils.convertRgbToHsv(color)[1]
        satRange = [self.saturationVal - (saturationRangeFloat / 2), self.saturationVal + (saturationRangeFloat / 2)]
        satRange = self._colorRangeClamp(satRange)
        self.saturationRange = satRange
        self.saturationRangeFloat = saturationRangeFloat
        self.setColor(color)  # Updates color too

    def setHueRangeColor(self, color, hueRangeFloat):
        self.hueVal = colorutils.convertRgbToHsv(color)[0]
        self.hueRange = [self.hueVal - (hueRangeFloat / 2), self.hueVal + (hueRangeFloat / 2)]
        self.hueRangeFloat = hueRangeFloat
        self.setColor(color)  # Updates color too

    def setAffectShells(self, affectShells):
        self.affectShells = affectShells

    def setShaderBaseName(self, shaderBaseName):
        self.shaderBaseName = shaderBaseName

    def setShaderType(self, shaderType):
        self.shaderType = shaderType

    def setRenderer(self, renderer):
        self.renderer = renderer

    def setSuffix(self, suffix):
        self.suffix = suffix

    def shadersColorable(self):
        return self.knownShaders

    # -------------------
    # LOGIC - HSV SLIDER CODE
    # -------------------

    def lockColor(self, color):
        """Records the current color as a HSV color and single values for easy access

        :param color: The current color from the UI, no randomization.
        :type color: list(float)
        """
        self.lockHsvColor = colorutils.convertRgbToHsv(color)
        self.color = color

    def updateHue(self, hueRangeFloat):
        """Used by sliders to interactively update the hue range of the randomize colors

        See self.updateSaturation() for the math.

        :param hueRangeFloat: The hue range to randomize as a single float
        :type hueRangeFloat: float
        """
        if not self.nodeList or not self.shaderInstances:
            return
        for i, inst in enumerate(self.shaderInstances):
            hsvColor = colorutils.convertRgbToHsv(inst.diffuse())
            multiplier = self.colMultipliers[i][0]
            newHue = self.lockHsvColor[0]
            if hueRangeFloat:  # check for non-zero value
                newHue = self.lockHsvColor[0] + (hueRangeFloat * multiplier)
            newHue = self._fixHueValue(newHue)
            newHsvColor = [newHue, hsvColor[1], hsvColor[2]]
            inst.setDiffuse(colorutils.convertHsvToRgb(newHsvColor))

    def updateSaturation(self, saturationRangeFloat):
        """Used by sliders to interactively update the saturation range of the randomize colors

        Math is:

            colSat = 0.9  # the initial color saturation
            curSat = 0.95  # the current color saturation
            rangeSatFloat = 0.2  # the current range of saturation
            diff = curSat - colSat  # the difference between the initial and current saturation
            multiply = diff / rangeSatFloat  # the multiply value to use in the new calculation
            newValue = colSat + (rangeX * multiply)  # the new result

        :param saturationRangeFloat: The saturation range to randomize as a single float
        :type saturationRangeFloat: float
        """
        if not self.nodeList or not self.shaderInstances:
            return
        for i, inst in enumerate(self.shaderInstances):
            hsvColor = colorutils.convertRgbToHsv(inst.diffuse())
            multiplier = self.colMultipliers[i][1]
            newSat = self.lockHsvColor[1]
            if saturationRangeFloat:  # check for non-zero value
                newSat = self.lockHsvColor[1] + (saturationRangeFloat * multiplier)
            newSat = self._clampSingleValue(newSat)
            newHsvColor = [hsvColor[0], newSat, hsvColor[2]]
            inst.setDiffuse(colorutils.convertHsvToRgb(newHsvColor))

    def updateValue(self, valueRangeFloat):
        """Used by sliders to interactively update the value range of the randomize colors

        See self.updateSaturation() for the math.

        :param valueRangeFloat: The value range to randomize as a single float
        :type valueRangeFloat: float
        """
        if not self.nodeList or not self.shaderInstances:
            return
        for i, inst in enumerate(self.shaderInstances):
            hsvColor = colorutils.convertRgbToHsv(inst.diffuse())
            multiplier = self.colMultipliers[i][2]
            newVal = self.lockHsvColor[2]
            if valueRangeFloat:  # check for non-zero value
                newVal = newVal + (valueRangeFloat * multiplier)
            newVal = self._clampSingleValue(newVal)
            newHsvColor = [hsvColor[0], hsvColor[1], newVal]
            inst.setDiffuse(colorutils.convertHsvToRgb(newHsvColor))

    # ----------------
    # LOGIC - COLORS
    # ----------------

    def updateColor(self, color):
        """Updates the main color to randomize.

        :param color: The color to randomize in sRGB float (0.5, 0.5, 0.5)
        :type color: list(float)
        """
        oldHSVColor = colorutils.convertRgbToHsv(self.color)
        updatedHSVColor = colorutils.convertRgbToHsv(color)
        if not self.shaderInstances:
            self.color = color
            return
        for i, inst in enumerate(self.shaderInstances):
            currentHSV = colorutils.convertRgbToHsv(inst.diffuse())
            offsetHSV = (oldHSVColor[0] - currentHSV[0],
                         oldHSVColor[1] - currentHSV[1],
                         oldHSVColor[2] - currentHSV[2])

            newHsvColor = (updatedHSVColor[0] - offsetHSV[0],
                           updatedHSVColor[1] - offsetHSV[1],
                           updatedHSVColor[2] - offsetHSV[2])
            newHsvColor = self._fixHSV(newHsvColor)
            inst.setDiffuse(colorutils.convertHsvToRgb(newHsvColor))
        self.color = color

    def _multiplierMath(self, cur, orig, floatRange):
        """Example:
            (h - self.hueVal) / self.hueRangeFloat"""
        if floatRange:
            return (cur - orig) / floatRange
        else:
            return cur - orig

    def _calcColMultiplier(self, color):
        """Used when the color multipliers don't exist (shaders added) create them, single color"""
        hsv = colorutils.convertRgbToHsv(color)
        hMultiplier = self._multiplierMath(hsv[0], self.hueVal, self.hueRangeFloat)
        sMultiplier = self._multiplierMath(hsv[1], self.saturationVal, self.saturationRangeFloat)
        vMultiplier = self._multiplierMath(hsv[2], self.valueVal, self.valueRangeFloat)
        return [hMultiplier, sMultiplier, vMultiplier]

    def _calcColMultipliers(self):
        """Used when the color multipliers don't exist (shaders added) create them. Creates self.colMultipliers"""
        self.colMultipliers = list()
        for shadInst in self.shaderInstances:
            color = shadInst.diffuse()
            if not color:
                return False  # texture found
            colMultipliers = self._calcColMultiplier(color)
            self.colMultipliers.append(colMultipliers)
        return True

    def _generateRandomColor(self):
        """Create a single random color from the global hsv ranged.

        :return: The random color in linear float
        :rtype: list(float)
        :return color: A list of the color multipliers need by the slider interaction
        :rtype colMultipliers: list(float)
        """
        h = random.uniform(self.hueRange[0], self.hueRange[1])  # randomize hue
        s = random.uniform(self.saturationRange[0], self.saturationRange[1])  # randomize saturation
        v = random.uniform(self.valueRange[0], self.valueRange[1])  # randomize saturation
        hMultiplier = self._multiplierMath(h, self.hueVal, self.hueRangeFloat)
        sMultiplier = self._multiplierMath(s, self.saturationVal, self.saturationRangeFloat)
        vMultiplier = self._multiplierMath(v, self.valueVal, self.valueRangeFloat)
        color = colorutils.convertHsvToRgb([h, s, v])
        return color, [hMultiplier, sMultiplier, vMultiplier]

    def _createColors(self):
        """Creates the colors and assigns them to the shader instances"""
        self.colMultipliers = list()
        if not self.shaderInstances:
            return
        for i in range(0, self.shaderAmount):
            color, colMultipliers = self._generateRandomColor()
            self.colMultipliers.append(colMultipliers)
            if self.shaderInstances[i].exists():
                self.shaderInstances[i].setDiffuse(color)
            else:
                self.shaderInstances[i].diffuseVal = color

    def _colorRangeClamp(self, colRange):
        """Clamps colors for value and saturation for color ranges

        :param colRange: a color range [0.1, 0.9]
        :type colRange: list(float)

        :return: The adjusted range
        :rtype: list(float)
        """
        if colRange[0] < 0.0:
            colRange[0] = 0.0
        if colRange[1] > 1.0:
            colRange[1] = 1.0
        return colRange

    def _clampSingleValue(self, value):
        """Clamps saturation and value (brightness) to fall withing 0.0 and 1.0.

        :param value: either a single saturation or value (brightness) value
        :type value: float

        :return: The adjusted saturation or value
        :rtype: float
        """
        if value <= 0.0:
            value = 0.001  # for sat don't want to reset hue
        if value > 1.0:
            value = 1.0
        return value

    def _fixHueValue(self, hueValue):
        """Fixes hue values under 0.0 and over 360.0

        :param hueValue: The hue as a float
        :type hueValue: float

        :return: The adjusted hue
        :rtype: float
        """
        if hueValue > 360.0:
            return hueValue - 360.0
        elif hueValue < 0.0:
            return hueValue + 360.0
        return hueValue

    def _fixHSV(self, hsvColor):
        """Clamps saturation and value and fixes hue values under zero and over 360"""
        return [self._fixHueValue(hsvColor[0]),
                self._clampSingleValue(hsvColor[1]),
                self._clampSingleValue(hsvColor[2])]

    # ----------------
    # LOGIC - DATA GENERAL
    # ----------------

    def _shaderInstances(self):
        """Creates empty shader instances, shaders are not created yet"""
        self.shaderInstances = list()
        for i in range(0, self.shaderAmount):
            self.shaderInstances.append(shadermulti.createShaderInstanceType(self.shaderType, shaderName=""))
            self.shaderInstances[i].specColorVal = self.specularColor  # zero specular

    def _createShaderNames(self):
        """Creates and assigns the shader names to the shader instances"""
        shaderNames = list()
        if not self.shaderInstances:
            return
        for i, inst in enumerate(self.shaderInstances):
            shadName = "_".join([self.shaderBaseName, str(i + 1).zfill(2)])  # create name with 2 padding
            if cmds.objExists(shadName):  # If not unique then fix with 2 padding
                shadName = namehandling.nonUniqueNameNumber(shadName, shortNewName=True, paddingDefault=2)
            inst.setShaderName(shadName)
            shaderNames.append(shadName)
        return shaderNames

    def _randomizeObjects(self):
        """Randomizes the object list by shuffling the list randomly"""
        if not self.nodeList:
            return  # can't create list without objects
        # Check for deleted nodes
        missingNodes = list()
        for node in self.nodeList:
            if not node.exists():
                missingNodes.append(node)
        if missingNodes:
            self.nodeList = [x for x in self.nodeList if x not in missingNodes]  # self.nodeList - missingNodes
        random.shuffle(self.nodeList)

    def assignShaders(self):
        """Assigns the shaders, assumes all preparation of the data has completed"""
        if not self.nodeShaderList:
            self.nodeShaderList = list(split(self.nodeList, self.shaderAmount))
        for i, shadInst in enumerate(self.shaderInstances):
            if not shadInst.exists():
                shadInst.createShader()
            shadInst.assign(zapi.fullNames(self.nodeShaderList[i]))  # assign a shader to the object

    def updateShaderAmount(self, shaderAmount):
        """Updates the amount of shaders used in the randomize.  And deletes or creates new shaders.

        :param shaderAmount: The amount of shaders to distribute for the randomize.
        :type shaderAmount: int
        """
        self.shaderAmount = shaderAmount
        if not self.shaderInstances:
            return  # Can't create list without shader instances
        self.nodeShaderList = list(split(self.nodeList, self.shaderAmount))  # see split() in this module
        # Update Instances -------------------------------------------
        numberOfInstances = len(self.shaderInstances)
        if self.shaderAmount == numberOfInstances:
            self.assignShaders()  # likely assigning to the same objects
            return
        elif self.shaderAmount < numberOfInstances:  # Delete the extra shader instances
            extraInstancesNumber = numberOfInstances - self.shaderAmount
            for inst in self.shaderInstances[-extraInstancesNumber:]:
                inst.deleteShader()
            del self.shaderInstances[-extraInstancesNumber:]
            del self.colMultipliers[-extraInstancesNumber:]
        else:  # self.shaderAmount < numberOfInstances. # Add the extra shader instances
            newInstancesNumber = self.shaderAmount - numberOfInstances
            for i in range(newInstancesNumber):
                inst = shadermulti.createShaderInstanceType(self.shaderType)
                self.shaderInstances.append(inst)
                color, colMultipliers = self._generateRandomColor()
                self.colMultipliers.append(colMultipliers)
                inst.setDiffuse(color)
                inst.setSpecColor(self.specularColor)  # zero specular
        # Assign From Instances -------------------------------------------
        self.assignShaders()
        self._createShaderNames()  # Rename all shaders

    def updateShaderNames(self, shaderBaseName):
        """Renames all the shader names on existing shaders if they exist"""
        self.shaderBaseName = shaderBaseName
        if not self.nodeList or not self.shaderInstances:
            return
        shaderNames = self._createShaderNames()
        output.displayInfo("Shaders renamed: {}".format(shaderNames))

    def reseedColors(self):
        """Reseeds/randomizes the colors and update applies them to all objects"""
        if not self.nodeList:
            return  # can't create list without objects
        if len(self.shaderInstances) != self.shaderAmount:
            self._updateData(reseedAssignments=False, reseedColors=True)
            return
        self._createColors()
        self.assignShaders()

    def reseedAssignments(self):
        """Reseed/Randomizes the object/shader assignments and applies them to all objects"""
        if not self.nodeList:
            return  # can't create list without objects
        if len(self.shaderInstances) != self.shaderAmount:
            self._updateData(reseedAssignments=True, reseedColors=False)
            return
        self._randomizeObjects()
        self.nodeShaderList = list(split(self.nodeList, self.shaderAmount))  # see split() in this module
        self.assignShaders()

    def averageColor(self, colorList):
        """Finds the average color of a list, colors can be None and the list can be empty

        :param colorList: A list of colors, some entries can be None or the list can be empty.
        :type colorList:
        :return averageColor: The average color of all the colors, can return an empty list
        :rtype averageColor:
        """
        newColList = list()
        if not colorList:
            return list()
        # Remove None entries -------------
        for col in colorList:
            if col:
                newColList.append(col)
        if not newColList:
            return list()
        colorCount = len(newColList)
        r = 0
        g = 0
        b = 0
        for color in newColList:
            r += color[0]
            g += color[1]
            b += color[2]
        if r:
            r = r/float(colorCount)
        if g:
            g = g/float(colorCount)
        if b:
            b = b/float(colorCount)
        return [r, g, b]

    def useShaders(self):
        """Uses the selected shaders and adds them to randomize

        :return shaderAmount: The amount of shaders found
        :rtype shaderAmount: int
        :return shaderAverageColor: The Average color of the shaders
        :rtype shaderAverageColor: list(float)
        """
        uknownShaders = list()
        shaderAverageColor = list()
        shaderColors = list()
        selObjs = cmds.ls(selection=True, long=True)
        if not selObjs:
            output.displayWarning("No objects or shaders are selected, please select.")
            return 0, shaderAverageColor
        self.useShadersBool = True
        # Get shaders from the current selection ------------------------
        shaders = shaderutils.getShadersFromNodes(selObjs)
        # Ingest the shaders as instances if possible and record diffuse colors ---------------
        self.shaderInstances = list()
        for shader in shaders:
            inst = shadermulti.shaderInstanceFromShader(shader)  # ingest shader
            if not inst.knownShader():  # some shaders are not color adjustable, so will disable UI colors if so.
                self.knownShaders = False
                uknownShaders.append(shader)
            col = inst.diffuse()
            if col:
                shaderColors.append(col)
            self.shaderInstances.append(inst)
        if not self.shaderInstances:
            output.displayWarning("No shaders found.")
            return 0, shaderAverageColor
        # Calculate the average color if known shaders ----------------
        if shaderColors:
            shaderAverageColor = self.averageColor(shaderColors)
        else:
            shaderAverageColor = (0.5, 0.5, 0.5)
        # Update amount -------------------
        self.shaderAmount = len(self.shaderInstances)
        # Update hsv multipliers --------------
        texturesFound = False
        if not uknownShaders:
            texturesFound = not self._calcColMultipliers()  # creates all the hsv multipliers required for the sliders
        if texturesFound:
            output.displayInfo("Information: Please select objects. Note colors cannot be changed as textures present.")
        elif uknownShaders:
            output.displayInfo("Information: Please select objects. Note colors cannot be changed. "
                                  "Zoo unsupported shader/s have been added {}.".format(uknownShaders))
        else:
            output.displayInfo("Information: Please select objects. Shaders have been added: {}".format(shaders))
        self.shadersWereSelected = True
        return self.shaderAmount, shaderAverageColor

    def _updateData(self, reseedAssignments=True, reseedColors=True):
        """Will recreate the data required for the random assignment.

        Mainly creates self.objShaderList which matches the self.shaderInstances

            self.shaderInstances: [shadInstance1, shadInstance2, shadInstance3]
            self.objShaderList: [["pCube1"], ["pSphere1", "pSphere2"], ["pCylinder5"]]

        :param reseedAssignments: re-randomize the object shader assignments?
        :type reseedAssignments: bool
        :param reseedColors: re-randomize the colors?
        :type reseedColors: bool
        """
        if not self.nodeList:
            return  # can't create list without objects
        self._shaderInstances()  # updates the list of shader instances
        self._createShaderNames()  # updates the shader names
        if reseedAssignments:
            self._randomizeObjects()  # shuffles self.nodeList
        if reseedColors:
            self._createColors()
        self.nodeShaderList = list(split(self.nodeList, self.shaderAmount))  # see split() in this module

    def randomizeShaders(self):
        """This button starts the randomize, will assign the shaders but is not used in updating.
        """
        if not self.nodeList:
            self.setSelectedObjs()
            if not self.nodeList:
                output.displayWarning("No Objects are selected, please select objects")
                return  # can't assign shaders without objects
        self.shadersWereSelected = False
        # Updates self.shaderInstances, self.objShaderList, and seeds objects and colors -------------------
        if not self.useShadersBool:  # Generate new shaders
            self._updateData(reseedAssignments=True, reseedColors=True)
        # Do the assignment ----------------------------------------------------------------------------------
        self.assignShaders()

    def clearCache(self):
        """Resets the cache fresh, deletes the randomize and shader data"""
        self.nodeList = list()
        self.objList = list()
        self.shaderInstances = list()
        self.nodeShaderList = list(list())
        self.knownShaders = True
        self.useShadersBool = False
        output.displayInfo("Information: Shader/object information cleared.")

    def exists(self):
        """Returns whether the current instance contains data

        :return exists: Does the data exist?
        :rtype exists: bool
        """
        if self.shaderInstances:
            return True
        return False
