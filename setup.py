from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="itfinderjob",
    version="0.1.0",
    author="Edgar Poghosyan",
    author_email="edgar.poghosyan.2031@gmail.com",
    description="Job search aggregator with Telegram bot integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edgar2031/itfinderjob",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.6",
        "python-dotenv>=1.0.0",
        "flask>=2.0.0",
        "requests>=2.26.0",  # If your project makes HTTP requests
        "beautifulsoup4>=4.10.0",  # If you do web scraping
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "flake8>=4.0.0",
            "black>=22.0.0",
        ],
        "prod": [
            "waitress>=2.0.0",
            "gunicorn>=20.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "itfinderjob=server:run_server",
        ],
    },
)