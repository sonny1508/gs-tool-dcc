from zoo.libs.hive import api
from zoo.libs.maya.utils import mayatestutils


class TestRoboBall(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("robo_ball")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestNatalie(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("natalie")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)

class TestTortoise(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("tortoise_toon")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestRobot(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("robot")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)



class TestBiped(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("biped_lightweight")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestMannequin(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("zoo_mannequin")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestArm(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestArmThreeFinger(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_three_finger")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)



class TestArmThreeFingerNmc(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_three_finger_nmc")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)


class TestArmNmc(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("arm_nmc")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)

class TestUEMannequin(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("ue5_mannequin")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)

class TestSirMoustache(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def test_create(self):
        config = api.Configuration()
        reg = config.templateRegistry()
        templatePath = reg.templatePath("sir_moustache")
        r, _ = api.loadFromTemplateFile(templatePath)
        self.assertIsInstance(r, api.Rig)
        api.commands.buildGuides(r)
        api.commands.polishRig(r)