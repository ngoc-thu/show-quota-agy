from setuptools import setup, find_packages

setup(
    name="antigravity-quota-monitor",
    version="1.0.0",
    description="Real-time Google Antigravity Quota Monitor on Ubuntu GNOME Desktop",
    author="Antigravity Team",
    packages=find_packages(),
    scripts=["antigravity-quota"],
    install_requires=[],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "antigravity-quota = src.cli.main:main",
        ],
    },
)
