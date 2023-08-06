import inspect

def decorate(func):
    # See explanation below
    lines = inspect.stack(context=2)[1].code_context
    decorated = any(line.startswith('@') for line in lines)
    print(func.__name__, 'was decorated with "@decorate":', decorated)
    return func

@decorate
def bar():
    pass

def foo():
    pass

# foo = decorate(foo)
@decorate
class MyDict(dict):
    pass