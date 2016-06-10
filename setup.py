from setuptools import setup, find_packages


VERSION = '1.0.0'


setup(
    name='borgmatic',
    version=VERSION,
    description='A wrapper script for Borg backup software that creates and prunes backups',
    author='Dan Helfman',
    author_email='witten@torsion.org',
    url='https://torsion.org/borgmatic',
    download_url='https://torsion.org/hg/borgmatic/archive/%s.tar.gz' % VERSION,
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
            'borgmatic = borgmatic.command:main',
        ]
    },
    obsoletes=[
        'atticmatic',
    ],
    tests_require=(
        'flexmock',
        'pytest',
    )
)
