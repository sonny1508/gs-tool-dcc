from zoo.preferences.core import preference


def shaderInterface():
    """ Shader Interface

    :return: Returns the preference interface "shader_interface"
    :rtype: :class:`preferences.interface.shader_interface.ShaderPreference`
    """
    return preference.interface("shader_interface")
