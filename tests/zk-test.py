from kazoo.client import KazooClient

zk = KazooClient(hosts='10.103.47.192:2181')
zk.start()

path = '/test'
print('---- create')
r = zk.create(path, b'hello shi', makepath=True)  # 自动创建父节点
print(r)

print('---- exist')
d = zk.exists(path) # 如不存在，返回None
print(d)

print('---- get')
d = zk.get(path) # 如不存在，则抛异常 kazoo.exceptions.NoNodeError
print(d)
print(d[0].decode('utf-8'))

print('---- set')
# 如不存在，则抛异常 kazoo.exceptions.NoNodeError
r = zk.set(path, b'hello world')
print(r)

print('---- delete')
# 不管存不存在，都可以删除
r = zk.delete(path, recursive=True)
print(r)

def my_leader_function():
    print('leader')

# election = zk.Election("/electionpath", "my-identifier")
# # blocks until the election is won, then calls
# election.run(my_leader_function)