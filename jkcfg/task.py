from datetime import timedelta

from pyutilb import SchedulerThread
from pyutilb.util import get_var
from wakaq import WakaQ, Queue, CronTask
from wakaq.worker import Worker
from pyutilb.log import log
from jkcfg.zkcfg import Zkcfg

# 获得redis连接
redis_host = get_var('redis_host', False) # 读命令行选项
if redis_host is None: # 读配置
    config = Zkcfg.read_config()
    redis_host = config['redis_host']
redis_host, redis_port = redis_host.split(':')

# 任务队列
wakaq = WakaQ(
    # redis server
    host=redis_host,
    port=int(redis_port),

    # List your queues and their priorities.
    # Queues can be defined as Queue instances, tuples, or just a str.
    queues=[
        #(0, 'test-queue'),
        'jkcfg-queue',
        #Queue('another-queue', priority=3, max_retries=5, soft_timeout=300, hard_timeout=360),
    ],

    # Number of worker processes. Must be an int or str which evaluates to an
    # int. The variable "cores" is replaced with the number of processors on
    # the current machine.
    concurrency="cores*4",

    # Raise SoftTimeout in a task if it runs longer than 30 seconds. Can also be set per
    # task or queue. If no soft timeout set, tasks can run forever.
    soft_timeout=30,  # seconds

    # SIGKILL a task if it runs longer than 1 minute. Can be set per task or queue.
    hard_timeout=timedelta(minutes=1),

    # If the task soft timeouts, retry up to 3 times. Max retries comes first
    # from the task decorator if set, next from the Queue's max_retries,
    # lastly from the option below. If No max_retries is found, the task
    # is not retried on a soft timeout.
    max_retries=3,

    # Combat memory leaks by reloading a worker (the one using the most RAM),
    # when the total machine RAM usage is at or greater than 98%.
    max_mem_percent=98,

    # Combat memory leaks by reloading a worker after it's processed 5000 tasks.
    max_tasks_per_worker=5000,

    # Schedule two tasks, the first runs every minute, the second once every ten minutes.
    # Scheduled tasks can be passed as CronTask instances or tuples.
    schedules=[

        # # Runs mytask on the queue with priority 1.
        # CronTask('* * * * *', 'mytask', queue='test-queue', args=[2, 2], kwargs={}),
        #
        # # Runs mytask once every 5 minutes.
        # ('*/5 * * * *', 'mytask', [1, 1], {}),
        #
        # # Runs anothertask on the default lowest priority queue.
        # ('*/10 * * * *', 'anothertask'),
    ],
)

# 任务: 同步配置到zk
# @wakaq.task(queue='test-queue', max_retries=7, soft_timeout=420, hard_timeout=480)
@wakaq.task
def sync_zk_config():
    log.info('worker执行任务: sync_zk_config')
    cfg = Zkcfg()
    cfg.sync()
    cfg.close()

# 生成同步任务
def produce():
    print("通知同步")
    sync_zk_config.delay()

# 启动同步任务worker
def start_worker():
    # 启动同步的定时任务
    sync_interval = config.get('sync_interval', 0)
    if sync_interval > 0:
        print("启动同步的定时任务")
        t = SchedulerThread()
        t.add_cron_job(f"*/{sync_interval} * * * * *", sync_zk_config)
    # 启动同步任务worker
    print('启动同步任务worker')
    worker = Worker(wakaq=wakaq)
    worker.start()

if __name__ == '__main__':
    produce()
    start_worker()
