from setuptools import setup, find_packages

setup(
    name="myblog",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "flask-migrate",
        "flask-login",
        "flask-wtf",
        "flask-mail",
        "python-dotenv",
        "markdown",
        "bleach",
        "pillow",
        "pytest",
        "pytest-cov",
        "pytest-flask",
    ],
) 