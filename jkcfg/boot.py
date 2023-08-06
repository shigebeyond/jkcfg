#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from optparse import OptionParser
from pyutilb.file import read_init_file_meta
from pyutilb.util import set_var

from jkcfg.zkcfg import Zkcfg
from jkcfg import task

# 解析命令的选项与参数
# :param name 命令名
# :param version 版本
# :return 命令选项+参数
def parse_cmd(name, version):
    # py文件外的参数
    args = sys.argv[1:]

    usage = f'''Usage: {name} [command] [options...]
    
Commands:
  pull          拉取最新配置文件
  sync          同步配置文件到zookeeper上
  diff          对比文件: 若指定文件, 则对比本地配置文件与zookeeper上的配置文件; 若未指定文件, 则对比本地git提交与zookeeper上的提交之间
  notify        通知配置的git仓库有更新
  work          启动worker, 监听配置的git仓库更新的通知, 并同步最新配置到zookeeper上
'''
    optParser = OptionParser(usage)

    # 添加选项规则
    # optParser.add_option("-h", "--help", dest="help", action="store_true") # 默认自带help
    optParser.add_option('-v', '--version', dest='version', action="store_true", help='Show version number and quit')
    optParser.add_option("-r", "--redis", dest="redis", type="string", help="redis server host and port")

    # 解析选项
    option, args = optParser.parse_args(args)

    # 输出帮助文档 -- 默认自带help
    if len(args) == 0: # or option.help == True:
        print(usage)
        sys.exit(1)

    # 输出版本
    if option.version == True:
        print(version)
        sys.exit(1)

    return option, args

# 拉取最新配置
def pull():
    cfg = Zkcfg()
    cfg.pull()

# 同步配置到zk
def sync():
    cfg = Zkcfg()
    cfg.sync()
    cfg.close()

# 对比文件
def diff(*args):
    cfg = Zkcfg()
    cfg.diff(*args)
    cfg.close()

# 通知同步: 生成同步任务
def notify():
    task.produce()

# 启动同步任务worker
def work():
    task.start_worker()

def main():
    # 读元数据：author/version/description
    dir = os.path.dirname(__file__)
    meta = read_init_file_meta(dir + os.sep + '__init__.py')
    # 解析命令
    option, args = parse_cmd('jkcfg', meta['version'])
    command = args[0]
    if command == 'notify' and option.redis != None:
        set_var('redis_host', option.redis)

    # 执行命令对应的函数
    funs = {
        'pull': pull,
        'sync': sync,
        'diff': diff,
        'notify': notify,
        'work': work,
    }
    if command not in funs:
        raise Exception(f'unknown command "{command}" for "jkcfg"')
    fun = funs[command]
    fun(*args[1:])

if __name__ == '__main__':
    main()
