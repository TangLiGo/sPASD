from DataOram import DataOramClient
import os
from math import log
import time
import random
import matplotlib.pyplot as plt

def test(blocks_num,branching):

    client = DataOramClient(blocks_num,blocks_num,branching,256)
    # generate dummy block

    record=dict()

    test_num=800
    for i in range(test_num):
        block_id =random.randint(0,blocks_num-1)#tests_data[i][0]#
        data =os.urandom(32)#tests_data[i][1]#
      #  print("write to",block_id)
       # print("write block:{} with:{}".format(block_id, data))
        client.write(block_id, data)
        #print("after write block:{} with:{}".format(block_id, data))
        record[block_id]=data
        # print(client.server.data_area)
        # print(record)
        # if client.read(block_id)[0]!=record[block_id]:
        #     raise Exception("Wrong",client.read(block_id),record[block_id])
    print("Success")


# start = time.time()
# for i in range(5):
#     test(16384,branching=8)
# end = time.time()
# print("time cost for branching={} is:{}".format(8,end-start))
start = time.time()
for i in range(5):
    test(32768,branching=10)
end = time.time()
print("time cost for branching={} is:{}".format(64,end-start))

#time cost for branching=8 is:376.72882986068726;
#time cost for branching=64 is:196.0236039161682.
#time cost for branching=8 is:303.88907504081726
#time cost for branching=64 is:132.40034198760986
#no aes
#time cost for branching=8 is:13.549620866775513
#time cost for branching=64 is:10.60214114189148