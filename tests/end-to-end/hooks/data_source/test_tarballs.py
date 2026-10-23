import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

import ruamel.yaml


def write_configuration(
    source_directory,
    config_path,
    repository_path,
    user_runtime_directory,
):
    '''
    Write out borgmatic configuration into a file at the config path. Set the options so as to work
    for testing. This includes injecting the given repository path, the user runtime directory to
    extract tarballs into, and encryption passphrase.
    '''
    config_yaml = f'''
source_directories:
    - {source_directory}
repositories:
    - path: {repository_path}
user_runtime_directory: {user_runtime_directory}

encryption_passphrase: "test"

tarballs:
    - name: tarball
      path: {user_runtime_directory}/test.tar.gz
'''

    with open(config_path, 'w') as config_file:
        config_file.write(config_yaml)

    return ruamel.yaml.YAML(typ='safe').load(config_yaml)


TEST_MEMBER_DATA = {
    'dir': {'type': tarfile.DIRTYPE, 'uid': 1, 'gid': 1, 'mode': 777, 'mtime': 12},
    'dir/foo.txt': {
        'type': tarfile.REGTYPE,
        'data': b'data',
        'uid': 2,
        'gid': 2,
        'mode': 755,
        'mtime': 34,
    },
    'link.txt': {
        'type': tarfile.SYMTYPE,
        'linkname': 'dir/foo.txt',
        'uid': 3,
        'gid': 3,
        'mode': 774,
        'mtime': 56,
    },
    'hard.txt': {
        'type': tarfile.LNKTYPE,
        'linkname': 'dir/foo.txt',
        'uid': 4,
        'gid': 4,
        'mode': 666,
        'mtime': 78,
    },
    'fifo': {'type': tarfile.FIFOTYPE, 'uid': 4, 'gid': 4, 'mode': 664, 'mtime': 90},
}


def create_test_tarballs(config):
    '''
    Create test tarballs for borgmatic to backup.
    '''
    for tarball in config['tarballs']:
        with tarfile.open(tarball['path'], mode='x:gz') as tar:
            for member_path, member_info in TEST_MEMBER_DATA.items():
                member = tarfile.TarInfo(name=member_path)
                member.type = member_info['type']
                link_name = member_info.get('linkname')

                if link_name is not None:
                    member.linkname = link_name

                member.uid = member_info.get('uid')
                member.gid = member_info.get('gid')
                member.mode = member_info.get('mode')
                member.mtime = member_info.get('mtime')
                file_data = member_info.get('data')

                if file_data is None:
                    tar.addfile(member)
                else:
                    member.size = len(file_data)
                    tar.addfile(member, fileobj=io.BytesIO(file_data))


def remove_test_tarballs(config):
    '''
    Remove the test tarballs in preparation for borgmatic restoring them.
    '''
    for tarball in config['tarballs']:
        os.remove(tarball['path'])


def check_test_tarballs(config):
    '''
    Check the contents of the test tarballs against the expected contents, e.g. after a restore to
    make sure they restored correctly.

    Raise if the tarballs don't check out.
    '''
    for tarball in config['tarballs']:
        with tarfile.open(tarball['path'], mode='r:gz') as tar:
            found_members = set()

            for extracted_member in tar:
                original_member_info = TEST_MEMBER_DATA[extracted_member.name]

                assert extracted_member.type == original_member_info['type']
                original_link_name = original_member_info.get('linkname')

                if original_link_name is not None:
                    assert extracted_member.linkname == original_link_name

                assert extracted_member.uid == original_member_info.get('uid')
                assert extracted_member.gid == original_member_info.get('gid')
                assert extracted_member.mode == original_member_info.get('mode')
                assert extracted_member.mtime == original_member_info.get('mtime')

                if extracted_member.type == tarfile.REGTYPE:
                    assert tar.extractfile(extracted_member).read() == original_member_info['data']

                found_members.add(extracted_member.name)

            assert found_members == set(TEST_MEMBER_DATA.keys())


def test_tarballs_dump_and_restore():
    temporary_directory = tempfile.mkdtemp()
    repository_path = os.path.join(temporary_directory, 'test.borg')
    original_working_directory = os.getcwd()

    try:
        config_path = os.path.join(temporary_directory, 'test.yaml')
        config = write_configuration(
            temporary_directory,
            config_path,
            repository_path,
            temporary_directory,
        )
        create_test_tarballs(config)
        check_test_tarballs(config)

        subprocess.check_call(
            [
                'borgmatic',
                '-v',
                '2',
                '--config',
                config_path,
                'repo-create',
                '--encryption',
                'repokey',
            ],
        )

        # Run borgmatic to generate a backup archive including tarballs.
        subprocess.check_call(['borgmatic', 'create', '--config', config_path, '-v', '2'])

        # Get the created archive name.
        output = subprocess.check_output(
            ['borgmatic', '--config', config_path, 'list', '--json'],
        ).decode(sys.stdout.encoding)
        parsed_output = json.loads(output)

        assert len(parsed_output) == 1
        assert len(parsed_output[0]['archives']) == 1
        archive_name = parsed_output[0]['archives'][0]['archive']

        # Restore the tarballs from the archive.
        remove_test_tarballs(config)
        subprocess.check_call(
            ['borgmatic', '-v', '2', '--config', config_path, 'restore', '--archive', archive_name],
        )

        # Ensure the test tarballs have actually been restored properly.
        check_test_tarballs(config)
    finally:
        os.chdir(original_working_directory)
        remove_test_tarballs(config)
        shutil.rmtree(temporary_directory)
