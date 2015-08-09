from setuptools import setup, find_packages


VERSION = '0.1.5'


setup(
    name='atticmatic',
    version=VERSION,
    description='A wrapper script for Attic/Borg backup software that creates and prunes backups',
    author='Dan Helfman',
    author_email='witten@torsion.org',
    url='https://torsion.org/atticmatic',
    download_url='https://torsion.org/hg/atticmatic/archive/%s.tar.gz' % VERSION,
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
            'atticmatic = atticmatic.command:main',
            'borgmatic = atticmatic.command:main',
        ]
    },
    tests_require=(
        'flexmock',
        'nose',
    )
)
