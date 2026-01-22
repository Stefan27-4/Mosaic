"""
Setup script for the RLM framework.
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("USER_GUIDE.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rlm-framework",
    version="0.1.0",
    author="Mosaic Contributors",
    description="Recursive Language Models framework for infinite context scaling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Stefan27-4/Mosaic",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
)
