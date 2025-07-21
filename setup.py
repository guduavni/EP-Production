from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ep-simulator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="ICAO English Proficiency Assessment Simulator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ep-simulator",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    python_requires=">=3.10",
    install_requires=[
        "Flask>=2.3.3",
        "Flask-Login>=0.6.2",
        "Flask-Admin>=1.6.1",
        "Flask-MongoEngine>=1.1.0",
        "mongoengine>=0.27.0",
        "python-dotenv>=1.0.0",
        "Werkzeug>=2.3.7",
        "openai>=0.28.1",
        "gunicorn>=21.2.0",
        "eventlet>=0.33.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "mypy>=1.5.1",
            "pylint>=2.17.5",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Flask",
    ],
    entry_points={
        "console_scripts": [
            "ep-simulator=app.cli:main",
        ],
    },
)
