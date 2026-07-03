"""Setup script for receipt-price-elasticity-promo-roi package."""

from setuptools import find_packages, setup
e
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="receipt-price-elasticity-promo-roi",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Price elasticity and promotional ROI analysis from receipt data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JawadKT/receipt-price-elasticity-promo-roi",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
)
