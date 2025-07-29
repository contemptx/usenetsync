from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="usenetsync",
    version="1.0.0",
    author="UsenetSync Team",
    description="Secure Usenet folder synchronization system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/usenetsync",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Usenet News",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "cryptography>=3.4.0",
        "psutil>=5.8.0",
        "PyYAML>=5.4.0",
        "tabulate>=0.8.0",
        "colorama>=0.4.4",  # For Windows color support
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
        "monitoring": [
            "matplotlib>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "usenetsync=cli:cli",
            "usync=cli:cli",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.md", "*.txt"],
    },
)