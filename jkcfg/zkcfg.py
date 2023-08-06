from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError
from pyutilb.file import *
from pyutilb.lazy import lazyproperty
from pyutilb.log import log
from jkcfg.gitrepo import GitRepo

# 同步zk上的配置数据
class Zkcfg(object):

    ZK_ROOT = '/jkcfg/' # 根节点
    ZK_LEADER = ZK_ROOT + 'leader' # 选举leader的节点
    ZK_COMMIT = ZK_ROOT + '_commit' # 记录最新提交的节点

    def __init__(self):
        # 仓库目录
        self.repo_path = os.path.join(os.getcwd(), 'repo')

        # 读配置文件
        self.config = self.read_config()

        # git仓库
        self.repo = GitRepo(self.repo_path, self.config['repo_url'], branch='master')
        # branch_list = self.repo.branches()
        # print(branch_list)
        # self.repo.change_to_branch('dev')

        # self.zk 延迟创建
        self.zk_connected = False

    # 读配置文件
    @classmethod
    def read_config(cls):
        config_file = os.path.join(os.getcwd(), 'jkcfg.yml')
        if not os.path.exists(config_file):
            raise Exception('缺少配置: ' + config_file)
        return read_yaml(config_file)

    # 延迟创建zk连接
    @lazyproperty
    def zk(self):
        # 连接zk
        zk = KazooClient(hosts=self.config['zk_hosts'])
        zk.start()
        self.zk_connected = True

        # 创建记录最新提交的节点
        if not zk.exists(self.ZK_COMMIT):
            zk.create(self.ZK_COMMIT, b'', makepath=True)  # 自动创建父节点
        return zk

    # 关闭时处理
    def close(self):
        # 与zk断开
        if self.zk_connected:
            self.zk.stop()

    # zk选举leader
    def elect_leader(self, callback):
        election = self.zk.Election(self.ZK_LEADER, "my-identifier")
        # blocks until the election is won, then calls
        # callback()
        election.run(callback)

    # --------------- 同步到zk --------------
    # 同步配置到zk
    def sync(self):
        # 拉取最新配置
        self.pull()
        # 获得2次git commit之间修改过的文件
        files = self.git_change_files()
        if not files:
            print("zk配置文件已是最新, 无需同步")
            return
        # 写zk节点
        n = len(files)
        print(f"有{n}个zk配置文件落后于本地, 逐个文件同步:")
        for f in files:
            action = self.set_zk_file(f)
            print(f'\t{action}: \033[31m{f}\033[0m')
        # 在zk上记录最新的git commit
        commit = self.local_commit()
        self.zk.set(self.ZK_COMMIT, commit.encode('utf-8'))

    # 从git仓库中拉取
    def pull(self):
        print('拉取最新配置')
        self.repo.pull()
        if not os.path.exists(self.repo_path):
            raise Exception('拉取失败: ' + self.yaml_repo_url)

    # 写zk文件(节点数据)
    def set_zk_file(self, path):
        file_path = os.path.join(self.repo_path, path)
        zk_path = self.ZK_ROOT + path
        if os.path.exists(file_path):  # 本地有: 更新zk节点
            content = read_file(file_path).encode('utf-8')  # 转bytes
            if not self.zk.exists(zk_path):  # 新增
                self.zk.create(zk_path, content, makepath=True)  # 自动创建父节点
                action = '创建'
            else:  # 修改
                self.zk.set(zk_path, content)
                action = '修改'
        else:  # 本地没有: 删除zk节点
            self.zk.delete(zk_path, recursive=True)
            action = '删除'
        return action

    # 读zk文件(节点数据)
    def get_zk_file(self, path):
        path = self.ZK_ROOT + path
        try:
            r = self.zk.get(path)
            return r[0].decode('utf-8')
        except NoNodeError as ex:
            return None

    # 下载zk文件(节点数据)到/tmp目录
    def download_zk_node(self, path):
        # 读
        data = self.get_zk_file(path) or ''
        # 只针对linux平台
        dir = '/tmp/jkcfg/'
        if not os.path.exists(dir):
            os.mkdir(dir)
        tmp_path = dir + path.replace('/', '-')
        write_file(tmp_path, data)
        return tmp_path

    # --------------- 对比 --------------
    # 对比文件
    def diff(self, *args):
        # 拉取最新配置
        self.pull()

        # 1 整体对比
        if len(args) == 0:
            files = self.git_change_files()
            if not files:
                print("zk配置文件已是最新")
                return
            n = len(files)
            print(f"有{n}个zk配置文件落后于本地:")
            for f in files:
                print(f'\t\033[31m{f}\033[0m')
            return

        # 2 对比单个文件
        path = args[0]
        f1 = os.path.join(self.repo_path, path) # 本地文件
        f2 = self.download_zk_node(path)  # zk配置文件
        self.diff_file(f1, f2)

    # 对比文件
    def diff_file(self, f1, f2):
        # 读配置的对比工具名，如 diff/vimdiff，更多对比工具参考 https://www.52dianzi.com/category/article/37/983777.html
        diff_tool = self.config.get('diff_tool', 'vimdiff')
        # 删除vim的swp文件
        if diff_tool == 'vimdiff':
            self.rm_vim_swp_file(f1)
            self.rm_vim_swp_file(f2)
        # 执行对比命令
        cmd = f"{diff_tool} {f1} {f2}"
        print(cmd)
        os.system(cmd)

    # 删除vim的swp文件
    def rm_vim_swp_file(self, path):
        dir, file = path.rsplit('/', 1)
        swp = f'{dir}/.{file}.swp'
        if os.path.exists(swp):
            os.remove(swp)

    # 获得本地commit与zk记录的commit之间修改过的文件
    def git_change_files(self):
        # zk记录的commit
        zk_commit = self.zk_commit()
        if zk_commit == '': # 如果zk为空, 则取所有文件
            return self.get_repo_files()
        if not self.repo.exist_commit(zk_commit):
            raise Exception(f'在本地仓库的git日志中找不到zk记录的commit[{zk_commit}], 请确保本地仓库已拉取最新配置')

        # 本地commit
        local_commit = self.local_commit()
        if local_commit == zk_commit:
            return []

        return self.repo.diff(local_commit, zk_commit)

    # zk记录的commit
    def zk_commit(self):
        zk_commit = self.zk.get(self.ZK_COMMIT)
        return zk_commit[0].decode('utf-8')

    # 本地commit
    def local_commit(self):
        return self.repo.last_commit()['commit']

    # 获得git仓库的所有文件
    def get_repo_files(self):
        r = []
        l = len(self.repo_path)
        for root, dirs, files in os.walk(self.repo_path, topdown=True):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                path = os.path.join(root, file)
                path = path[l+1:] # 干掉 self.repo_path, 只返回相对路径
                r.append(path)
        return r