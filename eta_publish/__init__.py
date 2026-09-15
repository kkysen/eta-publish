PACKAGE_NAME = __name__.replace("_", "-")
"""`eta_publish` spelled the way the distribution and the command are.

Derived rather than read back with `importlib.metadata.packages_distributions`,
which knows nothing of an editable install, which is how this is run.
"""
