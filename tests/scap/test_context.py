#!/usr/bin/env python2

import os
import shutil
import sys
import tempfile
import time
import unittest

from scap import context


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(suffix='-scap-test-dir')
        self.context = context.Context(self.root)

    def test_cleanup(self):
        os.mkdir(self.context.temp_path())
        with open(self.context.temp_path('foo'), 'w') as f:
            f.write('bar')

        self.context.cleanup()

        self.assertEqual(os.listdir(self.context.temp_path()), [])

    def test_path(self):
        self.assertEqual(self.context.path(), os.path.join(self.root))

    def test_path_joins_subpaths(self):
        self.assertEqual(self.context.path('foo', 'bar'),
                         os.path.join(self.root, 'foo', 'bar'))

    def test_setup(self):
        self.context.setup()

        self.assertTrue(os.path.exists(self.root))
        self.assertTrue(os.path.exists(self.context.temp_path()))

    def test_temp_path(self):
        path = self.context.temp_path()

        self.assertEqual(path, os.path.join(self.root, 'tmp'))

    def test_temp_path_joins_subpaths(self):
        path = self.context.temp_path('foo', 'bar')

        self.assertEqual(path, os.path.join(self.root, 'tmp/foo/bar'))

    def tearDown(self):
        shutil.rmtree(self.root)


class HostContextTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(suffix='-scap-test-dir')
        self.context = context.HostContext(self.root, environment='env1')

    def create_scap_file(self, *relpaths):
        def qualify(*relpaths):
            return os.path.join(self.root, 'scap', *relpaths)

        for i in range(1, len(relpaths)):
            parent_dir = qualify(*relpaths[:i])
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)

        path = qualify(*relpaths)

        with open(path, 'w') as f:
            f.write('')

        return path

    def create_scap_environment_file(self, *relpaths):
        return self.create_scap_file('environments', self.context.environment,
                                     *relpaths)

    def test_env_specific_path_with_default_file(self):
        self.context.setup()
        default_file = self.create_scap_file('foo')

        path = self.context.env_specific_path('foo')

        self.assertEqual(path, default_file)

    def test_env_specific_path_with_environment_file(self):
        self.context.setup()
        self.create_scap_file('foo')
        environment_file = self.create_scap_environment_file('foo')

        path = self.context.env_specific_path('foo')

        self.assertEqual(path, environment_file)

    def test_env_specific_paths(self):
        self.context.setup()
        default_file = self.create_scap_file('foo')
        default_dir = os.path.dirname(default_file)
        environment_file = self.create_scap_environment_file('foo')
        environment_dir = os.path.dirname(environment_file)

        paths = self.context.env_specific_paths()

        self.assertEqual(paths, [default_dir, environment_dir])

    def test_env_specific_paths_with_path(self):
        self.context.setup()
        default_file = self.create_scap_file('foo')
        environment_file = self.create_scap_environment_file('foo')

        paths = self.context.env_specific_paths('foo')

        self.assertEqual(paths, [default_file, environment_file])

    def test_env_specific_paths_filters_exists(self):
        self.context.setup()
        environment_file = self.create_scap_environment_file('foo')

        paths = self.context.env_specific_paths('foo')

        self.assertEqual(paths, [environment_file])

    def test_log_path(self):
        self.context.setup()

    def tearDown(self):
        shutil.rmtree(self.root)


class TargetContextTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(suffix='-scap-test-dir'))
        self.context = context.TargetContext(self.root)

    def create_rev_dir(self, rev):
        rev_dir = os.path.join(self.context.revs_dir, rev)
        os.mkdir(rev_dir)

        return rev_dir

    def create_rev_dirs(self, revs):
        rev_dirs = []

        for rev in revs:
            rev_dirs.append(self.create_rev_dir(rev))
            time.sleep(0.01)

        return rev_dirs

    def test_cache_dir(self):
        self.assertEqual(self.context.cache_dir,
                         os.path.join(self.root, 'cache'))

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_current_config_rev(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123_bar321'))
        self.context.use_config_rev('foo123')
        self.context.mark_rev_current('bar321')

        self.assertEqual(self.context.current_config_rev, 'foo123')

    def test_current_config_rev_with_no_current_rev(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123_bar321'))

        self.assertIsNone(self.context.current_config_rev)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_current_config_rev_with_no_config_rev(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123_bar321'))
        self.context.mark_rev_current('bar321')

        self.assertIsNone(self.context.current_config_rev)

    def test_current_link(self):
        self.assertEqual(self.context.current_link,
                         os.path.join(self.root, 'current'))

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_current_rev_dir(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123'))
        self.context.mark_rev_current('foo123')

        self.assertEqual(self.context.current_rev_dir,
                         os.path.join(self.root, 'revs/foo123'))

    def test_current_rev_dir_with_no_current_rev(self):
        self.context.setup()

        self.assertIsNone(self.context.current_rev_dir)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_current_rev_dir_with_deployed_config_rev(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123_bar123'))
        self.context.use_config_rev('foo123')
        self.context.mark_rev_current('bar123')

        self.assertEqual(self.context.current_rev_dir,
                         os.path.join(self.root, 'revs/foo123_bar123'))

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_done_rev_dir(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123'))
        self.context.mark_rev_done('foo123')

        self.assertEqual(self.context.done_rev_dir,
                         os.path.join(self.root, 'revs/foo123'))

    def test_done_rev_dir_with_no_rev_done(self):
        self.context.setup()
        os.mkdir(os.path.join(self.context.revs_dir, 'foo123'))

        self.assertIsNone(self.context.done_rev_dir)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_find_old_rev_dirs(self):
        self.context.setup()
        rev_dirs = self.create_rev_dirs([
            'foo1',  # old
            'foo2',  # old but current
            'foo3',  # old
            'foo4',  # old but done
            'foo5',
            'foo6',
            'foo7',
            'foo8',
            'foo9',
        ])

        self.context.mark_rev_current('foo2')
        self.context.mark_rev_done('foo4')

        old_rev_dirs = list(self.context.find_old_rev_dirs())

        self.assertEqual(len(old_rev_dirs), 2)
        self.assertEqual(old_rev_dirs, [rev_dirs[2], rev_dirs[0]])

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_link_path_to_rev(self):
        self.context.setup()
        rev_dir = self.create_rev_dir('foo123')
        temp_dir = tempfile.mkdtemp()
        final_path = os.path.join(temp_dir, 'bar')

        try:
            self.context.link_path_to_rev(final_path, 'foo123')
            self.assertTrue(os.path.exists(final_path))
            self.assertTrue(os.path.islink(final_path))
            self.assertEqual(os.path.realpath(final_path), rev_dir)
        finally:
            shutil.rmtree(temp_dir)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_link_path_to_rev_with_backup(self):
        self.context.setup()
        rev_dir = self.create_rev_dir('foo123')
        temp_dir = tempfile.mkdtemp()
        final_path = os.path.join(temp_dir, 'bar')

        os.mkdir(final_path)

        try:
            self.context.link_path_to_rev(final_path, 'foo123', backup=True)
            self.assertTrue(os.path.exists(final_path))
            self.assertTrue(os.path.islink(final_path))
            self.assertEqual(os.path.realpath(final_path), rev_dir)

            # Test that the path was backed up but don't bother trying to mock
            # the timestamp
            self.assertEqual(len(os.listdir(temp_dir)), 2)
        finally:
            shutil.rmtree(temp_dir)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_mark_rev_current(self):
        self.context.setup()
        rev_dir = self.create_rev_dir('foo1')

        self.context.mark_rev_current('foo1')

        self.assertTrue(os.path.islink(os.path.join(self.root, 'current')))
        self.assertEqual(os.path.realpath(self.context.current_link),
                         rev_dir)

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_mark_rev_done(self):
        self.context.setup()
        self.create_rev_dir('foo1')

        self.context.mark_rev_done('foo1')

        self.assertEqual(self.context.rev_done, 'foo1')

    @unittest.skipIf(sys.platform == 'darwin', 'Tests of `ln` fail on OS X')
    def test_mark_rev_in_progress(self):
        self.context.setup()
        self.create_rev_dir('foo1')

        self.context.mark_rev_in_progress('foo1')

        self.assertEqual(self.context.rev_in_progress, 'foo1')

    def test_rev_path(self):
        self.context.setup()

        self.assertEqual(self.context.rev_path('foo1'),
                         os.path.join(self.context.revs_dir, 'foo1'))

    def test_rev_path_with_saved_config_rev(self):
        self.context.setup()
        self.context.use_config_rev('bar2')

        self.assertEqual(self.context.rev_path('foo1'),
                         os.path.join(self.context.revs_dir, 'bar2_foo1'))

    def tearDown(self):
        shutil.rmtree(self.root)


if __name__ == '__main__':
    unittest.main()
