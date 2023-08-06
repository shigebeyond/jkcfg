from jkcfg.gitrepo import GitRepo

path = '/home/shi/code/java/jksoa'
repo = GitRepo(path, 'git@github.com:shigebeyond/jksoa.git', branch='master')

print('------ 分支')
print(repo.branches())

print('------ 最新一条提交')
print(repo.last_commit())

print('------ 提交')
print(repo.commits())

print('------ 对比2次提交件修改的文件:')
commit1 = 'be65a90c0d7e39403618dedb5439b983655c971d'
commit2 = '4be082a08f079e2b1cb777bcf43bde02c09fdad2'
r = repo.diff(commit1, commit2)
print(r)