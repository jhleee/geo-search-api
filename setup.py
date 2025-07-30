from setuptools import setup, find_packages

setup(
    name="geotag-search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "pydantic>=2.5.3",
        "python-multipart>=0.0.6",
        "numpy>=1.24.3",
    ],
    python_requires=">=3.8",
)