from setuptools import setup, find_namespace_packages

setup(
    name="repominify",
    version="0.1.0",
    author="Mike Casale",
    author_email="mike@casale.xyz",
    description="A Python package that optimizes codebase representations for LLMs by generating compact, context-rich summaries",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mikewcasale/repominify",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src", include=["*"]),
    python_requires=">=3.7",
    install_requires=[
        "networkx>=2.6.0",
        "pyyaml>=5.1.0",
    ],
    entry_points={
        "console_scripts": [
            "repominify=core.cli:main",
        ],
    },
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
