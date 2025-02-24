from zoo.libs.maya import triggers


class CustomSelectionTrigger(triggers.TriggerSelectionBase):
    """
    Lets create the trigger and print the first connected node

    .. code-block:: python
        # first register this plugin path before zoo loads or load zoo afterwards
        os.environ["ZOO_TRIGGER_COMMAND_PATH"] += ";currentPath to example/"
        # now reload or start zoo

        from zoo.libs.maya import triggers
        from zoo.libs.maya import zapi
        _testNode = zapi.createDag("TestTrigger", "transform")
        selectableNode = zapi.createDag("test", "transform")
        triggers = triggers.createSelectionTrigger([_testNode], "print(connected[0])",
                                        connectables=[selectableNode],
                                        triggerCommandId="customExampleTrigger"
                                        )
        zapi.select([_testNode])
        # result: test

    Now lets modify the custom command

    .. code-block:: python

        triggers[0].command().setCommandStr("print('helloworld')")
        zapi.select([_testNode])
        # result: helloworld

    # now lets add more nodes
        newNode = zapi.createDag("test2", "transform")
        cmd =triggers[0].command()
        cmd.addNodesToConnectables([newNode])
        print(list(cmd.connectedNodes()))
        #result: [<DagNode>test, <DagNode>test2]
    """
    id = "customExampleTrigger"

    def execute(self):
        # at this point before or after super we can run any code.
        print([i for i in self.connectedNodes()])
        # by calling super we ensure the custom python command on the node gets executed
        super(CustomSelectionTrigger, self).execute()
