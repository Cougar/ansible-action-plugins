"""docker_copy action plugin.

Source: https://github.com/ansible/ansible/issues/16586#issuecomment-231396197

"""
from os import path

from ansible.utils import boolean
from ansible.plugins.action import ActionBase
from ansible.plugins.action.copy import ActionModule as CopyActionModule

# pylint: disable=too-few-public-methods
class ActionModule(CopyActionModule, ActionBase):
    """docker_copy action_plugin."""

    FS_ROOT_DIR = '/'
    VOLUME_ROOT_DIR = 'var/lib/docker/volumes'
    COREOS_TOOLBOX_ROOT_DIR = '/media/root'

    def __fail(self, msg, tmp, task_vars):
        """Fail the action."""
        result = super(ActionModule, self).run(
            tmp=tmp, task_vars=task_vars)
        result['failed'] = True
        result['msg'] = msg
        return result

    def run(self, tmp=None, task_vars=None):
        """Handler for copy operations."""
        dest = self._task.args.pop('dest', None)
        if not dest:
            return self.__fail("dest is required", tmp, task_vars)

        if path.isabs(dest):
            return self.__fail(
                "dest must be a relative path", tmp, task_vars)

        volume = self._task.args.pop('volume', None)
        if not volume:
            return self.__fail("volume is required", tmp, task_vars)

        fs_root = getattr(self, 'FS_ROOT_DIR')
        if boolean.boolean(self._task.args.pop('coreos_toolbox', False)):
            fs_root = getattr(self, 'COREOS_TOOLBOX_ROOT_DIR')

        volume_dir = path.join(fs_root, getattr(self, 'VOLUME_ROOT_DIR'))
        volume_dir_stat = self._execute_remote_stat(
            volume_dir, all_vars=task_vars, tmp=tmp,
            follow=boolean.boolean(self._task.args.get('follow', False)))
        if not (volume_dir_stat['exists'] and volume_dir_stat['isdir']):
            return self.__fail(
                "volume root {} does not exist, is docker installed?".format(volume_dir),
                tmp, task_vars)

        volume_root = path.join(volume_dir, volume, '_data')
        self._task.args['dest'] = path.join(volume_root, dest)

        volume_root_stat = self._execute_remote_stat(
            volume_root, all_vars=task_vars, tmp=tmp,
            follow=boolean.boolean(self._task.args.get('follow', False)))
        if not (volume_root_stat['exists'] and volume_root_stat['isdir']):
            return self.__fail(
                "volume {} does not exist".format(volume),
                tmp, task_vars)

        result = super(ActionModule, self).run(tmp=tmp, task_vars=task_vars)
        # Return the result unchanged
        return result
