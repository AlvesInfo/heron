def countdown(n):
    """function countdown"""
    while n > 0:
        n -= 1


if __name__ == "__main__":
    from threading import Thread
    import multiprocessing
    import time

    COUNT = 100_000_000

    start = time.time()
    countdown(COUNT)
    end = time.time()
    print(end - start)

    # t1 = Thread(target=countdown, args=(COUNT / 4,))
    # t2 = Thread(target=countdown, args=(COUNT / 4,))
    # t3 = Thread(target=countdown, args=(COUNT / 4,))
    # t4 = Thread(target=countdown, args=(COUNT / 4,))
    # start = time.time()
    # t1.start()
    # t2.start()
    # t3.start()
    # t4.start()
    # t1.join()
    # t2.join()
    # t3.join()
    # t4.join()
    # end = time.time()
    # print(end - start)

    start = time.time()
    with multiprocessing.Pool() as pool:
        pool.map(
            countdown,
            [
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,
                COUNT / 8,

            ],
        )

        pool.close()
        pool.join()

    end = time.time()
    print(end - start)
