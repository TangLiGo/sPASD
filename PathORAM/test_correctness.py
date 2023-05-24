from recursive_path_oram import RecursivePathOramClient, RecursivePathOramServer
import os
from math import log
import time
import random
import matplotlib.pyplot as plt

def test(data_block_num=500,position_compress=8,test_num=819):
    level = log(data_block_num, 2)
    if level != int(level):
        level += 1
    level = int(level)
    client = RecursivePathOramClient(level,Z=5, position_compress=position_compress)
    dummy_buckets = client.generate_initialize_block()
    server = RecursivePathOramServer(dummy_buckets)

    # generate dummy block
   # test_num = 123

    records=dict()
    for i in range(test_num):
        block_id,data=random.randint(0,data_block_num-1),os.urandom(16)
        client.write(block_id, data,server)
        records[block_id]=data
    for key in records:
        if records[key]!=client.read(key,server):
            raise Exception("Wrong",records[key],client.read(key,server))
    print("Success")



for i in range(1):
    test()
