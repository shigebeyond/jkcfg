import logging
logging.getLogger().setLevel('INFO') # 关掉debug日志
import os
from git.repo import Repo
from git.repo.fun import is_git_dir

class GitRepo(object):
    """
    git仓库管理
    """
    def __init__(self, local_path, repo_url, branch='master'):
        self.local_path = local_path
        self.repo_url = repo_url
        self.repo = None
        self.initial(repo_url, branch)

    def initial(self, repo_url, branch):
        """
        初始化git仓库
        :param repo_url:
        :param branch:
        :return:
        """
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)

        git_local_path = os.path.join(self.local_path, '.git')
        if not is_git_dir(git_local_path):
            self.repo = Repo.clone_from(repo_url, to_path=self.local_path, branch=branch)
        else:
            self.repo = Repo(self.local_path)

    def pull(self):
        """
        从线上拉最新代码
        :return:
        """
        self.repo.git.pull()

    def branches(self):
        """
        获取所有远程分支, 非本地分支
        :return:
        """
        branches = self.repo.remote().refs
        return [item.remote_head for item in branches if item.remote_head != 'HEAD']

    def exist_commit(self, commit_id):
        '''
        检查单个提交是否存在
        '''
        ret = self.repo.git.show(commit_id, '--format="%H"', '--no-patch')
        return not ret.startswith('fatal:')

    def last_commit(self):
        """
        最新一条提交
        :return:
        """
        commit_log = self._get_commit_log(1)
        if commit_log == '' or commit_log.startswith('fatal:'): # fatal: 您的当前分支 'master' 尚无任何提交
            return None
        return eval(commit_log)

    def commits(self):
        """
        获取所有提交记录
        :return:
        """
        commit_log = self._get_commit_log(50)
        log_list = commit_log.split("\n")
        return [eval(item) for item in log_list]

    def _get_commit_log(self, count):
        return self.repo.git.log('--pretty={"commit":"%h","author":"%an","summary":"%s","date":"%cd"}',
                                       max_count=count,
                                       date='format:%Y-%m-%d %H:%M')

    def diff(self, commit1, commit2):
        '''
        获得2次commit之间修改过的文件
        :param commit1
        :param commit2
        '''
        diff = self.repo.git.diff(commit1, commit2, '--name-only')
        return diff.split("\n")

    def tags(self):
        """
        获取所有tag
        :return:
        """
        return [tag.name for tag in self.repo.tags]

    def change_to_branch(self, branch):
        """
        切换分值
        :param branch:
        :return:
        """
        self.repo.git.checkout(branch)

    def change_to_commit(self, branch, commit):
        """
        切换commit
        :param branch:
        :param commit:
        :return:
        """
        self.change_to_branch(branch=branch)
        self.repo.git.reset('--hard', commit)

    def change_to_tag(self, tag):
        """
        切换tag
        :param tag:
        :return:
        """
        self.repo.git.checkout(tag)

if __name__ == '__main__':
    remote_path = 'ssh://git@git.shikee.com:6023/xdz_product/test_yaml'
    local_path = os.path.join('yamlrepo', 'test')
    repo = GitRepo(local_path, remote_path)
    branch_list = repo.branches()
    print(branch_list)
    # repo.change_to_branch('dev')
    repo.pull()