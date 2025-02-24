import sys
import trace


def traceFunction(func, filePath):
    """Traces and outputs all calls to a file, useful for finding crash points.

    .. code-block:: python

        traceFunction(crashing_function, "/home/trace.txt")

    :param func: The function object to trace.
    :param filePath: The filePath to output.
    :type filePath: str
    """
    oldOut = sys.stdout
    oldErr = sys.stderr

    try:
        with open(filePath, "w") as f:
            sys.stdout = f
            sys.stderr = f
            tracer = trace.Trace(count=False, trace=True)
            tracer.runfunc(func)

    finally:
        sys.stdout = oldOut
        sys.stderr = oldErr
