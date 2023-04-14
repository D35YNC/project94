#!/usr/bin/python3

from setuptools import setup, find_packages
import project94

if __name__ == '__main__':
    setup(name="project94",
          version=project94.__version__,
          description="Reverse shell manager",
          long_description=open("./README.md", 'r').read(),
          long_description_content_type="text/markdown",
          author="D35YNC",
          url="https://github.com/d35ync/project94",
          classifiers=["Development Status :: 5 - Production/Stable",
                       "Environment :: Console",
                       "License :: OSI Approved :: MIT License",
                       "Topic :: Security",
                       "Programming Language :: Python"
                       "Programming Language :: Python :: 3.10"],
          python_requires=">=3.8",
          packages=find_packages(),
          install_requires=[line.strip() for line in open("./requirements.txt", "r").readlines()],
          entry_points={'console_scripts': ['project94 = project94:entry']})
