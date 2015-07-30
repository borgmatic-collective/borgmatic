from setuptools import setup, find_packages

setup(
    name='atticmatic',
    version='0.1.4',
    description='A wrapper script for Attic/Borg backup software that creates and prunes backups',
    author='Dan Helfman',
    author_email='witten@torsion.org',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'atticmatic = atticmatic.command:main',
            'borgmatic = atticmatic.command:main',
        ]
    },
    tests_require=(
        'flexmock',
        'nose',
    )
)
