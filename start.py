import time
import main
from multiprocessing import Process
x = []
for i in range(10):
    p1 = Process(target=main.main, args=(i,))
    p1.start()
    x.append(p1)
for i in x:
    i.join()
