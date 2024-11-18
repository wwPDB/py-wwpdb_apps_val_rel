# File: setup.py
# Date: 6-Oct-2018
#
# Update:
#
import re
import glob

from setuptools import find_packages
from setuptools import setup

packages = []
thisPackage = 'wwpdb.apps.val_rel'

with open('wwpdb/apps/val_rel/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


setup(
    name=thisPackage,
    version=version,
    description='wwPDB validation processing for weekly release',
    long_description="See:  README.md",
    author='Ezra Peisach',
    author_email='ezra.peisach@rcsb.org',
    url='https://github.com/wwpdb/py-wwpdb_apps_val_rel',
    #
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    #
    install_requires=['wwpdb.utils.config ~= 0.24', 'wwpdb.utils.detach',
                      'wwpdb.utils.dp', 'wwpdb.utils.message_queue ~= 0.6',
                      'wwpdb.apps.validation~=2.40', 'wwpdb.io~=0.15',
                      'wwpdb.utils.ws_utils', 'oslo_concurrency',
                      'wwpdb.utils.nmr', 'requests', 'mmcif',
                      'urllib3'
                      ],
    packages=find_packages(exclude=['wwpdb.apps.tests-val_rel',
                                    'mock-data']),
    # Enables Manifest to be used
    #include_package_data = True,
    package_data={
        # If any package contains *.md or *.rst ...  files, include them:
        '': ['*.md', '*.rst', "*.txt", "*.cfg"],
    },
    #
    # These basic tests require no database services -
    test_suite="wwpdb.apps.tests-val_rel",
    tests_require=['tox'],
    #
    # Not configured ...
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    # Added for
    command_options={
        'build_sphinx': {
            'project': ('setup.py', thisPackage),
            'version': ('setup.py', version),
            'release': ('setup.py', version)
        }
    },
    # This setting for namespace package support -
    zip_safe=False,
)
