# import asyncio
# import concurrent.futures
import multiprocessing
import pandas as pd
import queue
import time

def my_task(seed, q_msg, q_data):
    # print('task1 called', flush=True)
    print(f'task {seed} called')
    
    for i in range(10000):
        # data = str(i)
        # data = [i*j for j in range(5)]
        keys = ['abc','def5','ghi12','jkl0987','mno']
        values = [seed*i/(j+1) for j in range(5)]
        # data = dict(zip(keys, values))
        data = pd.DataFrame.from_dict(dict(zip(keys, values)), orient='index')
        q_data.put_nowait(data)

        time.sleep(0.1)

        try:
            msg = q_msg.get_nowait()
        # except asyncio.QueueEmpty:
        except queue.Empty:
            continue

        if msg == 'stop': break

        q_msg.task_done()
    
    q_msg.task_done()

    print(f'task {seed} done')

    return None

# def task2():
#     pass

if __name__ == '__main__':
    # q_msg_1 = asyncio.Queue()
    # q_data_1 = asyncio.Queue()
    # q_msg_1 = queue.Queue()
    # q_data_1 = queue.Queue()
    # q_msg_1 = multiprocessing.Queue()
    # q_data_1 = multiprocessing.Queue()
    q_msg_1 = multiprocessing.JoinableQueue()
    q_data_1 = multiprocessing.JoinableQueue()

    q_msg_2 = multiprocessing.JoinableQueue()
    q_data_2 = multiprocessing.JoinableQueue()

    # executor = concurrent.futures.ProcessPoolExecutor()
    # future1 = executor.submit(task1, q_msg_1, q_data_1)
    p1 = multiprocessing.Process(target=my_task, args=(3.7, q_msg_1, q_data_1))
    p2 = multiprocessing.Process(target=my_task, args=(8.6, q_msg_2, q_data_2))
    p1.start()
    p2.start()

    for i in range(10):
        time.sleep(0.3)

        try:
            data1 = q_data_1.get_nowait()
        # except asyncio.QueueEmpty:
        except queue.Empty:
            pass
        else:
            print(f'data1={data1}')
            print(type(data1))
            q_data_1.task_done()

        try:
            data2 = q_data_2.get_nowait()
        # except asyncio.QueueEmpty:
        except queue.Empty:
            pass
        else:
            print(f'data2={data2}')
            q_data_2.task_done()

        # print(f'i = {i}')

    q_msg_1.put_nowait('stop')
    q_msg_2.put_nowait('stop')

    q_msg_1.join()
    q_msg_2.join()

    # q_data_1.join()
    # q_data_2.join()

    # executor.shutdown
    p1.join()
    p2.join()
