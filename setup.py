from setuptools import setup, find_packages

setup(
    name='os-lang',
    version='0.1.0',
    packages=['src'],
    install_requires=[
        'llvmlite',
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'osc=src.main:main',
            'osc-gui=gui:main_gui',
        ],
    },
    author='Manus AI',
    description='Next-Generation OS Development Language Compiler',
)
