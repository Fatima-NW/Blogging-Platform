from setuptools import setup, find_packages

setup(
    name="mylogger",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["colorama>=0.4.6"],
    description="Reusable, colorful logging package for Python",
    author="Fatima Nadeem",
    python_requires=">=3.9",
)
