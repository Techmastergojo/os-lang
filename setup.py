from setuptools import setup, find_packages

setup(
    name='os-lang',
    version='0.1.2',
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
    author="Hamza Tehseen Cheema",
    author_email="founder@nexus-os.org",
    description='Next-Generation OS Development Language Compiler',
)
