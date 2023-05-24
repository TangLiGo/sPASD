from runningcode_nyc_spatial import getLoadTime,getOCCTime,getAnalyticalLoad,getAnalyticalOCC,getAnalyticalLoadTime,getAnalyticalOCCTime
import os
from math import log
import time
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
repeatTimes = 50
def collectRunningInfo_var_u(n,threshold,branches,time_type='occ'):
    print("Entering function: collectRunningInfo_var_u(n:{},dataset_th:{},branches:{},time_type:{})".format(n,threshold,branches,time_type))
    costs = []
    us_range=[2**i for i in range(8)]
    ws=[500,1000]

    for w in ws:#list(range(64, 700, 128)):
        print("processing n:{}, w_prop:{}, branches:{}".format(n,w,branches))

        if os.path.exists('data/with_initialization_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy'):
            sub_costs = np.load('data/with_initialization_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy', allow_pickle=True)
        else:
            sub_costs = []
            for u in us_range:

                if time_type=='occ':
                    server_storage_cost, client_storage_cost, res = getOCCTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                elif time_type=='load':
                    server_storage_cost, client_storage_cost, res = getLoadTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                else:
                    raise Exception("time_type can only be 'occ' or 'load")

                sub_costs.append([u, server_storage_cost,client_storage_cost,res])
            np.save('data/with_initialization_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy', sub_costs)
        time_records=[sub_costs[i][3].mean(axis=0)[0]/w for i in range(len(sub_costs))]
        print("w:{}; u range:{}".format(w,[sub_costs[i][0] for i in range(len(sub_costs))]) )
        print("average time cost (per w):",time_records)
        results=[sub_costs[i][3].mean(axis=0) for i in range(len(sub_costs))]

        print("average requests:{}".format([result[1] for result in results]))
        print("data acces:{}".format([result[2] for result in results]))
        print("data_block_byte:{}".format([result[3] for result in results]))
        print("pos access:{}".format([result[4] for result in results]))
        print("pos_block_byte:{}".format([result[5] for result in results]))
        print("average bandwidth:", [result[2]*result[3]+result[4]*result[5] for result in results])
        print("server storage cost:{}, client storage cost:{}".format([sub_costs[i][1] for i in range(len(sub_costs))],[sub_costs[i][2] for i in range(len(sub_costs))]))

        costs.append([n, w, sub_costs])


def collectRunningInfo_var_w(n,threshold,branches,time_type='occ'):
    print(
        "Entering function: collectRunningInfo_var_w(n:{},dataset_th:{},branches:{},time_type:{})".format(n, threshold,
                                                                                                          branches,
                                                                                                          time_type))

    plt.figure()
    ws=[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    for u_order in [0,5]:
        u = 2 ** u_order
        print("u:{}".format(u))
        if os.path.exists('data/with_initialization_var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy'):
            costs = np.load('data/with_initialization_var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy', allow_pickle=True)
        else:
            costs = []
            # 164,3440
            for w in ws:
                # n=2**n_order
              #  w = int(w_prop * n)
                if time_type == 'occ':
                    server_storage_cost, client_storage_cost, res = getOCCTime(n, u, w, threshold=threshold,
                                                                               repeatTimes=repeatTimes,
                                                                               branches=branches)
                elif time_type == 'load':
                    server_storage_cost, client_storage_cost, res = getLoadTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                else:
                    raise Exception("time_type can only be 'occ' or 'load")

                costs.append([w, server_storage_cost, client_storage_cost, res])
            np.save('data/with_initialization_var_w_results' + time_type + '_n' + str(n) + '_u' + str(u) + '_b' + str(
                branches) + '_nyc_spatial.npy', costs)
        time_records=[costs[i][3].mean(axis=0)[0] for i in range(len(costs))]
        print("u:{}; w range:{}".format(u,[costs[i][0] for i in range(len(costs))]) )
        print("average time cost:",time_records)
        results=[costs[i][3].mean(axis=0) for i in range(len(costs))]

        print("average requests:{}".format([result[1] for result in results]))
        print("data acces:{}".format([result[2] for result in results]))
        print("data_block_byte:{}".format([result[3] for result in results]))
        print("pos access:{}".format([result[4] for result in results]))
        print("pos_block_byte:{}".format([result[5] for result in results]))
        print("average bandwidth:", [result[2]*result[3]+result[4]*result[5] for result in results])
        print("server storage cost:{}, client storage cost:{}".format([costs[i][1] for i in range(len(costs))],[costs[i][2] for i in range(len(costs))]))

def collectRunningInfo_var_n(threshold,branches):
    print(
        "Entering function: collectRunningInfo_var_n(dataset_th:{},branches:{}".format( threshold,
                                                                                                          branches))

    plt.figure()
    n_orders=list(range(10,21,2))
    w=1
    for u_order in [0,4]:
        u = 2 ** u_order

        if False:#os.path.exists('data/with_initialization_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy'):
            costs = np.load('data/with_initialization_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy', allow_pickle=True)
        else:
            costs = []
            # 164,3440
            for n_order in n_orders:
                n=2**n_order

                server_storage_cost, client_storage_cost, res = getLoadTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                costs.append([n_order, server_storage_cost, client_storage_cost, res])
            np.save('data/with_initialization_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy', costs)
        time_records=[costs[i][3].mean(axis=0)[0]/costs[i][0] for i in range(len(costs))]
        print("u:{}; n_order range:{}".format(u,[costs[i][0] for i in range(len(costs))]) )
        print("average time cost (per w):",time_records)
        results=[costs[i][3].mean(axis=0) for i in range(len(costs))]



        print("average requests:{}".format([result[1] for result in results]))
        print("data acces:{}".format([result[2] for result in results]))
        print("data_block_byte:{}".format([result[3] for result in results]))
        print("pos access:{}".format([result[4] for result in results]))
        print("pos_block_byte:{}".format([result[5] for result in results]))
        print("average bandwidth:", [result[2]*result[3]+result[4]*result[5] for result in results])
        print("server storage cost:{}, client storage cost:{}".format([costs[i][1] for i in range(len(costs))],[costs[i][2] for i in range(len(costs))]))


def showAnalyticalOCCTime(branching):
    costs = []
    n = 16384
    us_range=list(range(1,64))#list(range(8))#[2**i for i in range(8)]
    w_props=[0.01,0.03,0.05]

    for w_prop in w_props:#list(range(64, 700, 128)):
        sub_costs=[]
        w=int(w_prop*n)
        for u in us_range:
           # u = 2 ** i
            temp = getAnalyticalOCCTime(n, u, w, branching=branching) / w
            sub_costs.append([u, temp])
        print("w_prop={}, analytical occ time:{}".format(w,sub_costs))
        costs.append([n, w, sub_costs])
        plt.figure()
        plt.plot([cost[1] for cost in sub_costs])
        plt.show()

def showAnalyticalOCCTime_var_w(branching):
    costs = []
    n = 16384
    us_range=list(range(1,64))#list(range(8))#[2**i for i in range(8)]
    w_props=[0.01,0.03,0.05]
    u=1
    for w_prop in w_props:#list(range(64, 700, 128)):
        #sub_costs=[]
        w=int(w_prop*n)

        temp = getAnalyticalOCCTime(n, u, w, branching=branching)

        costs.append(temp)
    plt.figure()
    plt.plot(costs)
    plt.show()
def var_branches(threshold=2):
    branches_set = [10,16]
    print("Entering function: var_branches(), branches_set:", branches_set)
    n = 16384
    for branches in branches_set:
        print("get information for n:{},branches:{}".format(n,branches))
        collectRunningInfo_var_u(n, threshold=threshold, branches=branches, time_type='occ')
        collectRunningInfo_var_u(n, threshold=threshold, branches=branches, time_type='load')
       # collectRunningInfo_var_w(n, threshold=threshold, branches=branches,time_type='load')
      #  collectRunningInfo_var_w(n, threshold=threshold, branches=branches, time_type='occ')

    # for branches in branches_set:
    #     print("get information var n,branches:{}".format( branches))
    #     collectRunningInfo_var_n(threshold=threshold,branches=branches)



print("threshold = 2-------------------------")
var_branches(threshold=2)
#showAnalyticalOCCTime(8)
#showAnalyticalOCCTime_var_w()

