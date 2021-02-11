import asyncio
# from collections import deque

import numpy as np
import pandas as pd

async def data_producer(queue):
    l = list(range(10))

    for n in range(10):
        df = pd.DataFrame(np.array(l).reshape(-1, 5) + n)
        queue.put_nowait(df)
    
    # print(f'queue = {queue}')
    print(f'len = {queue.qsize()}')

    # await asyncio.sleep(1)

async def data_consumer(queue):
    # await asyncio.sleep(1)
    
    while True:
        item = await queue.get()
        print()
        print(f'item = {item}')

        queue.task_done()

async def main():
    queue = asyncio.Queue()
    
    tasks = []
    task = asyncio.create_task(data_producer(queue))
    tasks.append(task)
    task = asyncio.create_task(data_consumer(queue))
    tasks.append(task)

    await asyncio.sleep(1)

    # Wait until the queue is fully processed.
    await queue.join()

    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    asyncio.run(main())

