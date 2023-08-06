from git import Repo

path = '/home/shi/code/java/jksoa'
repo = Repo(path)
print('------ 分支:')
print(repo.branches)
for item in repo.branches:
    print(item.name)
# print(repo.active_branch) # 当前分支

print('------ 远程分支:')
for item in repo.remote().refs:
    print(item.remote_head)

print('------ 切换分支:')
# r = repo.git.checkout('master')
r = repo.git.checkout('3.0')
print(r)
print(repo.active_branch) # 当前分支

# print('------ 索引:')
# print(repo.index)

print('------ 远程仓库:')
print(repo.remotes)

print('------ git目录:')
print(repo.git_dir)
print(repo.working_tree_dir)

print('------ 当前提交:')
print(repo.description) # 当前提交

print('------ 拉取:')
r = repo.git.pull()
print(r)

print('------ 对比2次提交件修改的文件:')
commit1 = 'be65a90c0d7e39403618dedb5439b983655c971d'
commit2 = '4be082a08f079e2b1cb777bcf43bde02c09fdad2'
r = repo.git.diff(commit1, commit2, '--name-only')
print(r)