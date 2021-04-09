import asyncio
# import concurrent.futures
import multiprocessing
import pandas as pd
import queue
import time


async def data_producer(seed, q_data):
    print(f'data producer called')

    i = 0
    while True:
        # data = str(i)
        # data = [i*j for j in range(5)]
        keys = ['abc','def5','ghi12','jkl0987','mno']
        values = [seed*i/(j+1) for j in range(5)]
        # data = dict(zip(keys, values))
        data = pd.DataFrame.from_dict(dict(zip(keys, values)), orient='index')
        
        q_data.put_nowait(data)

        await asyncio.sleep(0.1)

        try:
            pass
        except asyncio.CancelledError:
            break
        
        i += 1

    print(f'data producer done')


async def my_async_main(seed, q_msg, q_data):
    print(f'async main called')

    async_task = asyncio.create_task( data_producer(seed, q_data) ) 

    while True:
        await asyncio.sleep(1)

        try:
            msg = q_msg.get_nowait()
        except queue.Empty:            
            continue

        if msg == 'stop': break

        q_msg.task_done()
    
    print(f'STOP message received!')

    async_task.cancel()

    q_msg.task_done()

    print(f'async main done')


def my_task(seed, q_msg, q_data):
    print(f'task {seed} called')

    asyncio.run(my_async_main(seed, q_msg, q_data), debug=True)    

    print(f'task {seed} done')


if __name__ == '__main__':
    q_msg_1 = multiprocessing.JoinableQueue()
    q_data_1 = multiprocessing.JoinableQueue()
    p1 = multiprocessing.Process(target=my_task, args=(3.7, q_msg_1, q_data_1))
    p1.start()

    # q_msg_2 = multiprocessing.JoinableQueue()
    # q_data_2 = multiprocessing.JoinableQueue()
    # p2 = multiprocessing.Process(target=my_task, args=(8.6, q_msg_2, q_data_2))
    # p2.start()

    for i in range(20):
        time.sleep(0.2)

        try:
            data = q_data_1.get_nowait()
        except queue.Empty:
            print('awaiting data1...')
        else:
            print(f'data={data}')
            # print(type(data))
            q_data_1.task_done()

    q_msg_1.put_nowait('stop')
    q_msg_1.join()
    # q_data_1.join()
    p1.join()

    # q_msg_2.put_nowait('stop')
    # q_msg_2.join()
    # q_data_2.join()
    # p2.join()
