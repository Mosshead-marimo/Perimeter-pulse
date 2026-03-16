# Placeholder for setup.py
from setuptools import setup, find_packages
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Read README
long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")

# Read requirements.txt
def read_requirements():
    req_file = BASE_DIR / "requirements.txt"
    requirements = []
    with open(req_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements


setup(
    name="firewall-log-analyzer",
    version="1.0.0",
    author="Kaushik Aadhithya Chiratanagandla",
    author_email="",
    description="AI-driven Windows Firewall Log Analyzer for Anomaly and Information Leakage Detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    license="MIT",

    packages=find_packages(exclude=("tests", "docs")),

    python_requires=">=3.10",

    install_requires=read_requirements(),

    extras_require={
        "dev": ["pytest"],
        "deep": ["tensorflow>=2.15.0"]
    },

    entry_points={
        "console_scripts": [
            "firewall-analyzer=scripts.analyze_logs:main"
        ]
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],

    include_package_data=True,
)
