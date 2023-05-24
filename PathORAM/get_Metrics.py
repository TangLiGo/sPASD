from recursive_path_oram import RecursivePathOramClient, RecursivePathOramServer
import os
from math import log
import time
import math
import random
def initialize(data_block_num=16384,position_compress=4,req_num=819):
    level = log(data_block_num, 2)
    if level != int(level):
        level += 1
    level = int(level)

    client = RecursivePathOramClient(level, position_compress=position_compress)
    # generate dummy block
    dummy_buckets = client.generate_initialize_block()
    print("client.blocks_size:", client.blocks_size)
    #改进后，其实server_tree_block_size=[math.ceil((client.block_id_size+client.levels[i]*client.position_compress) if i>0 else client.blocks_size[i])/ 256) * 256 for i in range(len(dummy_buckets))]
    server_tree_block_size=[math.ceil(client.blocks_size[i]*(client.position_compress if i>0 else 1)/ 256) * 256 for i in range(len(dummy_buckets))]
    print("tree block numbers",[len(dummy_buckets[i])  for i in range(len(dummy_buckets))])
    print("tree block sizes", server_tree_block_size)
    #server_trees_storage_cost=[len(dummy_buckets[i]) * math.ceil(client.blocks_size[i]*client.position_compress**(i>0)/ 256) * 256 for i in range(len(dummy_buckets))]
    server_trees_storage_cost=[len(dummy_buckets[i]) * math.ceil(client.blocks_size[i]*(client.position_compress if i>0 else 1)/ 256) * 256 for i in range(len(dummy_buckets))]
    print("server storage: recursive tree sizes (bit):", server_trees_storage_cost)
    print("server storage (byte)", client.Z * sum(server_trees_storage_cost)/8)
    print("position length", len(client.position_map), client.position_map)
    server = RecursivePathOramServer(dummy_buckets)
    # read and write test
   # req_num = 819
    # start_time=server.get_access_time()
    start_bandwidth=[server.count[i]*client.Z*server_tree_block_size[i] for i in range(client.recursive_level+1)]
    start = time.time()
    # write content to oram and record map between file and block_id
    # client.write(123, contents[0][1], server)
    for i in range(req_num):
        block_id = random.randint(0,data_block_num-1)
        data = os.urandom(16)
        client.write(block_id, data, server)
    # print("success",i)
    end = time.time()
    end_bandwidth=[server.count[i]*client.Z*server_tree_block_size[i] for i in range(client.recursive_level+1)]
    # end_time=server.get_access_time()
    # print("bndwidth", end_time,start_time,end_time-start_time,(end_time-start_time)*4048)
    print("self.max_stash_size", client.max_stash_size)
    print("bandwidth (all)", sum(end_bandwidth) - sum(start_bandwidth))
    print("average of write CPU time", (end - start) / req_num, "s")


initialize(req_num=10)
initialize(position_compress=32,req_num=10)
initialize(position_compress=256,req_num=10)


