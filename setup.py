from setuptools import setup, find_packages

setup(
    name="docgate",
    version="0.1.0",
    description="Document access system with authentication and payments",
    packages=find_packages(where="docgate"),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
    ],
    include_package_data=False,
    package_data={
    }
)
