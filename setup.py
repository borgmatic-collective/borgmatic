from setuptools import find_packages, setup

VERSION = '1.6.1'


setup(
    name='borgmatic',
    version=VERSION,
    description='Simple, configuration-driven backup software for servers and workstations',
    author='Dan Helfman',
    author_email='witten@torsion.org',
    url='https://torsion.org/borgmatic',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Topic :: Security :: Cryptography',
        'Topic :: System :: Archiving :: Backup',
    ],
    packages=find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': [
            'borgmatic = borgmatic.commands.borgmatic:main',
            'upgrade-borgmatic-config = borgmatic.commands.convert_config:main',
            'generate-borgmatic-config = borgmatic.commands.generate_config:main',
            'validate-borgmatic-config = borgmatic.commands.validate_config:main',
        ]
    },
    obsoletes=['atticmatic'],
    install_requires=(
        'jsonschema',
        'requests',
        'ruamel.yaml>0.15.0,<0.18.0',
        'setuptools',
        'colorama>=0.4.1,<0.5',
    ),
    include_package_data=True,
    python_requires='>3.7.0',
)
