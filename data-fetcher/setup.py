import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="uniliwue.datafetchersFETCHER_NAME", # Replace with your own username
    version="0.0.1",
    author="Uni Liechtenstein Team",
    author_email="uni.li-wue.projekt@protonmail.com",
    description="FETCHER_NAME Data Fetcher",
    long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://github.com/lirudayam/uni-li-wue-project-seminar",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={  # Optional
        'console_scripts': [
            'run=FETCHER_NAME:main',
        ],
    },
    install_requires=[
        "requests",
        "nltk",
        "web3"
    ],
    setup_requires=['wheel'],
    python_requires='>=3.6',
)
