import setuptools

setuptools.setup(
    name="dominionator",
    version="0.0.1",
    author="Tom Nixon",
    author_email="dominionator@tomn.co.uk",
    url="https://github.com/tomjnixon/dominionator",
    packages=setuptools.find_packages(),
    install_requires=["attrs~=19.1", "numpy~=1.16"],
)
