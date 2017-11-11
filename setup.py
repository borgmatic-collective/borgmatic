from setuptools import setup, find_packages


VERSION = '1.1.11'


setup(
    name='borgmatic',
    version=VERSION,
    description='A wrapper script for Borg backup software that creates and prunes backups',
    author='Dan Helfman',
    author_email='witten@torsion.org',
    url='https://torsion.org/borgmatic',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Topic :: Security :: Cryptography',
        'Topic :: System :: Archiving :: Backup',
    ),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'borgmatic = borgmatic.commands.borgmatic:main',
            'upgrade-borgmatic-config = borgmatic.commands.convert_config:main',
            'generate-borgmatic-config = borgmatic.commands.generate_config:main',
        ]
    },
    obsoletes=[
        'atticmatic',
    ],
    install_requires=(
        'pykwalify',
        'ruamel.yaml<=0.15',
        'setuptools',
    ),
    tests_require=(
        'flexmock',
        'pytest',
    ),
    include_package_data=True,
)
