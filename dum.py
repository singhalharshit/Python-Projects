# import asyncio

# async def task1():
#     print("I have started task 1")
#     await asyncio.sleep(2)
#     return "Task 1 done"

# async def task2():
#     print("I have started task 2")
#     await asyncio.sleep(1)
#     return "Task 2 done"

# async def main():
#     results = await asyncio.gather(task1(), task2())
#     print(results)

# asyncio.run(main())  



import asyncio

async def task(name, delay):
    await asyncio.sleep(delay)
    return f"{name} done"

async def main():
    results = await asyncio.gather(
        task("A", 2),
        task("B", 1),
        task("C", 3)
    )
    print(results)

asyncio.run(main())
