from DataOram import DataOramClient
import matplotlib.pyplot as plt
import os
from math import log
import time
import math
import random
def getAll(blocks_num=16384,branching=8,req_num=819):
    requests=[]
    for i in range(req_num):
        block_id = random.randint(0,blocks_num-1)
        data = os.urandom(32)
        requests.append([block_id, data])
    data_block_bytes=32
    client = DataOramClient(blocks_num,blocks_num,branching,data_block_bytes*8)
    # generate dummy block
    server_storage_cost= len(client.server.oram_blocks)*client.block_byte_size+len(client.position_map.pos_client.server.oram_blocks)*client.position_map.pos_node_bytes

    client_stash_storage_cost=client.position_map.pos_node_bytes*(client.position_map.posORAM_treelevel+1)*2
    client_position_map_cost = client.position_map.pos_node_bytes

    start_data_access_time,data_block_bytes,start_pos_access_time,pos_block_bytes=client.get_server_access_info()
    start = time.clock()
    # write content to oram and record map between file and block_id
    # client.write(123, contents[0][1], server)
    for i in range(req_num):
        client.write(requests[i][0], requests[i][1])
    # print("success",i)
    end = time.clock()
    end_data_access_time,data_block_bytes,end_pos_access_time,pos_block_bytes=client.get_server_access_info()

    bandwidth=(end_data_access_time-start_data_access_time)*data_block_bytes+(end_pos_access_time-start_pos_access_time)*pos_block_bytes
    CPUTime=(end - start) / req_num
    print("blocks_num={},branching={},server storage (byte)={}, client storage (byte)={}, bandwidth={},CPUTime={}".format(blocks_num,branching,server_storage_cost,client_stash_storage_cost,bandwidth,CPUTime))

    return data_block_bytes,pos_block_bytes,server_storage_cost,client_stash_storage_cost,bandwidth,CPUTime
def getStorageCost(blocks_num=16384,branching=8):
    data_block_bytes=32
    client = DataOramClient(blocks_num,blocks_num,branching=branching,data_block_bits=256)
    # generate dummy block
    server_storage_cost= len(client.server.oram_blocks)*client.block_byte_size+len(client.position_map.pos_client.server.oram_blocks)*client.position_map.pos_node_bytes
   # print("server storage (byte)", server_storage_cost)

    client_stash_storage_cost=client.position_map.pos_node_bytes*(client.position_map.posORAM_treelevel+1)*2
    client_position_map_cost = client.position_map.pos_node_bytes
#    print("position length", len(client.position_map), client.position_map)
    print("data block bytes={},pos block bytes={}".format(client.block_byte_size,client.position_map.pos_node_bytes))
    print("blocks_num={},branching={},server storage (byte)={}, client storage (byte)={}".format(blocks_num,branching,server_storage_cost,client_stash_storage_cost))
    return data_block_bytes,client.position_map.pos_node_bytes,server_storage_cost,client_stash_storage_cost
def observer_storage_var_branching(blocks_num,branchings):
    storage_costs=[]
    for branching in branchings:
        data_block_bytes,pos_block_bytes,server_storage_cost, client_storage_cost = getStorageCost(blocks_num=blocks_num,branching=branching)
        storage_costs.append([data_block_bytes,pos_block_bytes,server_storage_cost, client_storage_cost])
    return storage_costs
def observer_all_var_branching(blocks_num,branchings):
    costs=[]
    for branching in branchings:
        data_block_bytes,pos_block_bytes,server_storage_cost, client_storage_cost,bandwidth,CPUTime = getAll(blocks_num=blocks_num,branching=branching)
        costs.append([data_block_bytes,pos_block_bytes,server_storage_cost, client_storage_cost,bandwidth,CPUTime])
    return costs
def drawfigs(blocks_num=32768,branchings=[2, 4, 8, 16, 32, 64, 128]):
    blocks_num = 32768
    branchings = [2, 4, 8, 16, 32, 64, 128]
    # storage_costs=observer_storage_var_branching(blocks_num=blocks_num,branchings=branchings)
    # print("storage costs for branchings:{} is {}".format(branchings,storage_costs))
    # #blocks_num=16384 storage costs for branchings:[2, 4, 8, 16, 32, 64, 128] is [[8911936, 960], [2446336, 512], [1422976, 320], [1328128, 512], [1251328, 768], [1248256, 1536], [1245184, 3072]]
    #
    # plt.figure()
    # plt.subplot(2,1,1)
    # plt.plot([storage[0] for storage in storage_costs])
    # plt.subplot(2,1,2)
    # plt.plot([storage[1] for storage in storage_costs])
    costs = observer_all_var_branching(blocks_num=blocks_num, branchings=branchings)
    print(" costs for branchings:{} is {}".format(branchings, costs))
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot([cost[0] for cost in costs])
    plt.subplot(2, 1, 2)
    plt.plot([cost[1] for cost in costs])
    plt.title('Storage cost')
    plt.figure()
    plt.plot([cost[2] for cost in costs])
    plt.title('Bandwidth cost')
    plt.figure()
    plt.plot([cost[3] for cost in costs])
    plt.title('CPU time cost')
    plt.show()


def observe_var_branchings(blocks_num=32768):

    branchings = [8,9,10,16,32, 64, 128]
    costs = observer_storage_var_branching(blocks_num=blocks_num, branchings=branchings)
    print("data block bytes:{}".format([cost[0] for cost in costs]))
    print("pos block bytes:{}".format([cost[1] for cost in costs]))
    print("client storage cost:{}".format([cost[3] for cost in costs]))
  #  print("bandwidth cost:{}".format([cost[3] for cost in costs]))
    print("costs".format(costs))
blocks_num_set=[32768,65536,131072]
for blocks_num in blocks_num_set:
    observe_var_branchings(blocks_num)
