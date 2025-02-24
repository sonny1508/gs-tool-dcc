from maya import cmds

import maya.api.OpenMaya as om2

from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base



class ZooTubeCurve(base.MetaBase):
    """Class that controls the meta network node setup for the tube on curve functionality

    Found in zoo.libs.maya.cmds.rig.splines
    """
    _default_attrs = [{"name": "strokeTransform", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "meshTransform", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "meshShape", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "strokeShape", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "curve", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "group", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      ]

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooTubeCurve, self).metaAttributes()
        defaults.extend(ZooTubeCurve._default_attrs)
        return defaults

    def connectAttributes(self, strokeTransform, strokeShape, meshTransform, meshShape, brushNode, group, curve):
        """ Connects the maya nodes to the meta node

        :param strokeTransform:
        :type strokeTransform: zapi.DGNode
        :param strokeShape:
        :type strokeShape:
        :param meshTransform:
        :type meshTransform:
        :param meshShape:
        :type meshShape:
        :param brushNode:
        :type brushNode:
        :param group:
        :type group:
        :return:
        :rtype:
        """
        curve.message.connect(self.curve)
        meshTransform.message.connect(self.meshTransform)
        meshShape.message.connect(self.meshShape)
        strokeTransform.message.connect(self.strokeTransform)
        strokeShape.message.connect(self.strokeShape)
        group.message.connect(self.group)


    def bake(self):
        """ Bake

        :return:
        :rtype:
        """
        self.strokeTransform.source().node().delete()
        meshTransform = self.meshTransform.source().node()  # type: zapi.DagNode
        meshTransform.setParent(self.group.source().node().parent())
        self.group.source().node().delete()
        self.delete()

        # Delete attributes
        attrs = ["density", "radius", "axisDivisions", "minClip", "maxClip", "polyLimit"]
        [cmds.deleteAttr("{}.{}".format(meshTransform.fullPathName(), a)) for a in attrs]

    def deleteTube(self):
        """ Clean up

        :return:
        :rtype:
        """
        self.group.source().node().delete()
        self.delete()

    def setMetaAttributes(self, radius=None, axisDiv=None, density=None, minClip=None, maxClip=None, polyLimit=None):
        """Sets the setup's attributes usually from the UI"""
        meshTransform = self.meshTransform.source().node()  # type: zapi.DagNode
        values = {"density": density,
                  "radius": radius,
                  "axisDivisions": axisDiv,
                  "minClip": minClip,
                  "maxClip": maxClip,
                  "polyLimit": polyLimit
                  }

        for k, v in values.items():
            if v:
                # meshTransform.setAttribute(k, v)  # TODO bring this zapi code back once undo is handled
                cmds.setAttr(".".join([meshTransform.fullPathName(), k]), v)

    def tubeAttributes(self):
        """ Get the attributes of the tube

        :return:
        :rtype:
        """
        source = self.meshTransform.source()
        if source is None:
            return None
        meshTransform = self.meshTransform.source().node()
        return {"density": meshTransform.attribute("density").asFloat(),
                "radius": meshTransform.attribute("radius").asFloat(),
                "axisDivisions": meshTransform.attribute("axisDivisions").asInt(),
                "minClip": meshTransform.attribute("minClip").asFloat(),
                "maxClip": meshTransform.attribute("maxClip").asFloat(),
                "polyLimit": meshTransform.attribute("polyLimit").asInt()}




