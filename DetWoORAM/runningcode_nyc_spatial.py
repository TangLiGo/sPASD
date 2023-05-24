from DataOram import DataOramClient

import os
from math import log
import time
import matplotlib.pyplot as plt
from random import randint
import random
import math
import numpy as np
import scipy.stats as ss
import scipy.optimize as optimize
from data_processing import get_requests_set

def SP_initiation(SP_size,branches=2):
    # initialize oram
    client = DataOramClient(SP_size,SP_size,branches,data_block_bits=256)
    for id in range(SP_size):
        client.write(id,os.urandom(32))

    return client
def divide_SP_random(accessible_grid_IDs,u):
    random.shuffle(accessible_grid_IDs)
    grids_num=accessible_grid_IDs.shape[0]
    SP_division=[[accessible_grid_IDs[j] for j in range(i * int(grids_num / u), (i + 1) * int(grids_num / u))] for i in range(u)]
    cur_len = int(grids_num / u) * u
    for i in range(cur_len,grids_num):
        SP_division[i-cur_len].append(accessible_grid_IDs[i])
    return SP_division
def SPs_initiation(accessible_grid_IDs, u, v,branches=2):

    SPs = divide_SP_random(accessible_grid_IDs, u)
    clients=[]
    server_storage_cost,client_storage_cost=0,0
    SP_block_map = dict()
    for SP_id in range(len(SPs)):
        p_id=0
        for id in SPs[SP_id]:
            SP_block_map[id]=[SP_id,p_id]
            p_id+=1
        SP_client=SP_initiation(v, branches=branches)
        clients.append(SP_client)

    server_storage_cost = u*(len(clients[0].server.oram_blocks) * clients[0].block_byte_size + len(
            clients[0].position_map.pos_client.server.oram_blocks) * clients[0].position_map.pos_node_bytes)


    client_storage_cost=client_stash_storage_cost = u*clients[0].position_map.pos_node_bytes * (clients[0].position_map.posORAM_treelevel + 1) * 2
    client_position_map_cost = clients[0].position_map.pos_node_bytes

    return server_storage_cost,client_storage_cost,clients,SP_block_map
def divide_requests(requests,SP_map,u,v):
    requests_division=[[] for i in range(u)]
    for request in requests:
        #print("request",request)
        write_value=os.urandom(32)
        SP_id,p_id=SP_map[request]
        requests_division[SP_id].append([p_id,write_value,'write'])
    requests_uniform=requests_division
    max_num=max([len(req) for req in requests_division])

    for SP_id in range(u):
        while len(requests_uniform[SP_id])<max_num:
            write_value = os.urandom(32)
            requests_uniform[SP_id].append([randint(0,v-1),write_value, 'write'])
    return requests_uniform
def divide_merged_requests(requests,SP_map,u,v):
    requests_division=[[] for i in range(u)]
    requests_ids = [[] for i in range(u)]
    for request in requests:
        SP_id,p_id=SP_map[request]
        if p_id not in requests_ids[SP_id]:
            write_value = os.urandom(32)
            requests_division[SP_id].append([p_id, write_value, 'write'])
            requests_ids[SP_id].append(p_id)
    requests_uniform=requests_division
    max_num=max([len(req) for req in requests_division])
    #print("occ:",max_num*u)
    for SP_id in range(u):
        while len(requests_uniform[SP_id])<max_num:
            write_value = os.urandom(32)
            requests_uniform[SP_id].append([randint(0,v-1),write_value, 'write'])
    return requests_uniform
def SP_process_requests(requests,client):
    # test first time read
    start_data_access_time,data_block_bytes,start_pos_access_time,pos_block_bytes=client.get_server_access_info()
   # print("start_data_access_time,data_block_bytes,start_pos_access_time,pos_block_bytes",start_data_access_time,data_block_bytes,start_pos_access_time,pos_block_bytes)
    for request in requests:
        block_id = request[0]
        data = request[1]
        op=request[2]
        if op=='write':
            client.write(block_id, data)
        else:
         #   print(block_id,len(client.position_map),client.position_map)
            read_data = client.read(block_id)

    end_data_access_time, data_block_bytes, end_pos_access_time, pos_block_bytes = client.get_server_access_info()

    bandwidth= (end_data_access_time - start_data_access_time) * data_block_bytes + (
                    end_pos_access_time - start_pos_access_time) * pos_block_bytes
    return end_data_access_time - start_data_access_time,data_block_bytes,end_pos_access_time - start_pos_access_time,pos_block_bytes


def SPs_process_requests(SP_requests,clients):


    data_access_time,pos_access_time=0,0
    for i in range(len(clients)):
        data_access_time_temp,data_block_byte,pos_access_time_temp,pos_block_byte=SP_process_requests(SP_requests[i], clients[i])
        data_access_time+=data_access_time_temp
        pos_access_time+=pos_access_time_temp
      #  print("data_access_time_temp,data_block_byte,pos_access_time_temp,pos_block_byte",data_access_time_temp,data_block_byte,pos_access_time_temp,pos_block_byte)
   # print("data_access_time,data_block_byte,pos_access_time,pos_block_byte",data_access_time,data_block_byte,pos_access_time,pos_block_byte)
    return data_access_time,data_block_byte,pos_access_time,pos_block_byte


def balls_ino_bins_maxload(u,w):
    # if w>=u*log(u):
    #     return w/u+np.sqrt(2*w*np.log(u)/u)
    # else:
    #     return 0
    return w / u + np.sqrt(2 * w * np.log(u) / u)
    if w>=u*log(u):
        return w/u+np.sqrt(2*w*np.log(u)/u)
    else:
        return max(1,np.log(u)/np.log(u*log(u)/w)*(1+np.log(u*np.log(u)/w)**2/np.log(u*np.log(u)/w)))

        #raise Exception("un nature")
#  elif w>1:
  #     return 0.0012*log(u) / log(u / w)#随着u的增大而减小 系数是变化的
  # else:
    #    return  log(u)/log(log(u))

def getOCCTime(n, u, w,threshold=2,repeatTimes=20, branches=2):
  #  print("Entering function getOCCTime:(n:{},u:{},w:{},repeatTimes:{},branches:{})".format(n, u, w,repeatTimes, branches))

    req_sets, accessible_grid_IDs = get_requests_set(partition_num=n,threshold=threshold,req_num=w)
    chosen_sets_id=np.random.randint(0,req_sets.shape[0],repeatTimes)
    results=np.zeros([repeatTimes,6])
    repeat_ID=0

    v = math.ceil(n / u)


    server_storage_cost, client_storage_cost, pair_client_servers, SP_map = SPs_initiation(accessible_grid_IDs, u, v, branches=branches)

    for chosen_set_id in chosen_sets_id:
        requests=req_sets[chosen_set_id]
        merged_requests = divide_merged_requests(requests, SP_map, u, v)
       # print("req num:{}, merged_request num:{}".format(len(requests),len(merged_requests[0])*u))
       # print("merged_requests",merged_requests)
        start = time.clock()
        data_access_time,data_block_byte,pos_access_time,pos_block_byte=SPs_process_requests(merged_requests, pair_client_servers)
        end = time.clock()
      #  t+=end - start
        results[repeat_ID]=[end-start,len(merged_requests[0])*u,data_access_time,data_block_byte,pos_access_time,pos_block_byte]

      #  occ_req_num+=len(merged_requests[0])*u
        repeat_ID+=1
  #  print(results.mean(axis=0))
    return server_storage_cost,client_storage_cost,results
def getLoadTime(n, u, w,threshold=2,repeatTimes=20,branches=2):

  #  t = 0
  #  load_req_num = 0
    req_sets,accessible_grid_IDs= get_requests_set(partition_num=n,threshold=threshold,req_num=w)
    chosen_sets_id=np.random.randint(0,req_sets.shape[0],repeatTimes)
    results=np.zeros([repeatTimes,6])
    repeat_ID=0
    v = math.ceil(n / u)


    server_storage_cost, client_storage_cost, clients, SP_map = SPs_initiation(accessible_grid_IDs, u, v, branches=branches)

    for chosen_set_id in chosen_sets_id:
        requests=req_sets[chosen_set_id]
        SP_requests=divide_requests(requests,SP_map, u, v)
      #  print("req num:{}, SP_requests num:{}".format(len(requests), len(SP_requests[0]) * u))
        start = time.clock()
        data_access_time,data_block_byte,pos_access_time,pos_block_byte=SPs_process_requests(SP_requests, clients)
        end = time.clock()
      #  t += end - start
      #  load_req_num += len(SP_requests[0]) * u
        results[repeat_ID]=[end-start,len(SP_requests[0])*u,data_access_time,data_block_byte,pos_access_time,pos_block_byte]
        repeat_ID+=1


    return server_storage_cost,client_storage_cost,results#t / repeatTimes, load_req_num/repeatTimes



def getAnalyticalLoadTime(n, u, w,branching):

    max_load=max(1,balls_ino_bins_maxload(u, w))
    Np = int((math.ceil(n / u) - 2) / (branching - 1))
    t=max(max_load,1)*u*(-1 + 1 * log((Np+ 1)* (branching - 1) + 1, branching))#log(n/u,branching)#math.ceil(log(n/u,branching))

    return t
def getAnalyticalOCCTime(n, u, w, branching):

    max_load=balls_ino_bins_maxload(u, w)
    possibilities = [0.68, 0.27, 0.05]
    max_occ = sum([n / u / 3 * (1 - (1 - 3 * u / n) ** (max_load * possibilities[i])) for i in range(3)])
    occ= max(1, max_occ)
    Np=int((math.ceil(n/u) - 2) / (branching - 1) )
    t=occ*u*(-1 + 1 * log((Np+ 1)* (branching - 1) + 1, branching))#log(n/u,branching)#math.ceil(log(n/u,branching))
    return t
def getAnalyticalLoad(u,w):
    max_load = balls_ino_bins_maxload(u, w)
    return u*max_load
def getAnalyticalOCC(n,u,w):
    max_load = balls_ino_bins_maxload(u, w)
    possibilities=[0.68,0.27,0.05]
    max_occ=sum([n/u/3*(1-(1-3*u/n)**(max_load*possibilities[i])) for i in range(3)])
   # print("u*max(1,max_occ)",u*max(1,max_occ))
    return u*max(1,max_occ)