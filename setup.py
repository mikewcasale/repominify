from setuptools import setup, find_namespace_packages
import os
import re

def get_version():
    init_path = os.path.join("repominify", "__init__.py")
    try:
        with open(init_path, "r") as f:
            content = f.read()
            version_match = re.search(r'^__version__ = ["\']([^"\']*)["\']', content, re.M)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        pass
    
    # Fallback to hardcoded version if file not found
    return "0.1.4"

setup(
    name="repominify",
    version=get_version(),
    author="Mike Casale",
    author_email="mike@casale.xyz",
    description="A Python package that optimizes codebase representations for LLMs by generating compact, context-rich summaries",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mikewcasale/repominify",
    packages=find_namespace_packages(include=["repominify", "repominify.*"]),
    python_requires=">=3.7",
    install_requires=[
        "networkx>=2.6.0",
        "pyyaml>=5.1.0",
    ],
    entry_points={
        "console_scripts": [
            "repominify=repominify.cli:main",
        ],
    },
    package_data={
        "": ["py.typed"],
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
