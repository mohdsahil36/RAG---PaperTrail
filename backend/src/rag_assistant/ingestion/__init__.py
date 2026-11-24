# Why init file? Marks the directory as a regular Python package and manage how its modules are exposed to the outside world

# In case we do not have __init__.py file present , you have to specify the exact file names
# from math_tools.addition import add
# from math_tools.subtraction import subtract

# Inside math_tools/__init__.py
# from .addition import add
# from .subtraction import subtract

# Much cleaner code!
# from math_tools import add, subtract

# So __init__.py file acts as a gatekeeper between the actual files and the imports