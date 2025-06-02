from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="userchrome-loader",
    version="1.0.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'userchrome-loader=src.launcher:main',
        ],
    },
    author="orbital",
    description="A tool to load UserChrome scripts for Zen Browser",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/orbi-tal/userchrome-loader",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    extras_require={
        'gui': ['PyQt6>=6.8.0', 'PyQt6-sip>=13.9.1'],
    }
)
