import traceback

from zoovendor import six


def execute(script, locals_, globals_):
    script = script.replace(u"\u2029", "\n")
    script = six.ensure_str(script).strip()
    if not script:
        return {
            "reason": "InvalidScript",
            "message": "Provided Script is an empty string."
        }
    evalCode = True
    try:
        outputCode = compile(script, "<string>", "eval")
    except SyntaxError:
        evalCode = False
        try:
            outputCode = compile(script, "string", "exec")
        except SyntaxError:
            return {
                "reason": "errored",
                "traceback": traceback.format_exc()
            }

    # ok we've compiled the code now exec
    if evalCode:
        try:
            results = eval(outputCode, globals_, locals_)
            if results is not None:
                return {
                    "reason": "executed",
                    "message": results
                }
        except Exception:
            return {
                "reason": "errored",
                "traceback": traceback.format_exc()
            }
    else:
        try:
            exec(outputCode, globals_, locals_)
            return {
                "reason": "executed",
                "message": None
            }
        except Exception:
            return {
                "reason": "errored",
                "traceback": traceback.format_exc()
            }
