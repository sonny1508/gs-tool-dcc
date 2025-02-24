class Singleton(type):
    """Singleton metaclass that overrides the __call__ method and always returns a single class instance
    of the cls.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



class ObjectDict(dict):
    """Wrapper of the standard python dict operate like an object.

    .. code-block:: python

        a = ObjectDict({'channelBox': False,
                 'default': u'',
                 'isDynamic': True,
                 'keyable': False,
                 'locked': False,
                 'max': None,
                 'min': None,
                 'name': u'id',
                 'softMax': None,
                 'softMin': None,
                 'Type': 13, # type found from zoo.libs.maya.api.attrtypes
                 'value': u'mid'}
                 )
        a.max
        a.min

    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(ObjectDict, self).__getattribute__(item)

    def __setattr__(self, key, value):
        """Overridden to support property method overrides and "." syntax
        """
        propObj = getattr(self.__class__, key, None)
        if isinstance(propObj, property):
            if propObj.fset is None:
                raise AttributeError("can't set attribute")
            propObj.fset(self, value)
        else:
            self[key] = value

    def __delattr__(self, item):
        if item in self:
            del self[item]
            return
        super(ObjectDict, self).__delattr__(item)