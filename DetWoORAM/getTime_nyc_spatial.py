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
    us_range=[0]#[2**i for i in range(8)]
    ws=[100,500,1000]

    for w in ws:#list(range(64, 700, 128)):
        print("processing n:{}, w_prop:{}, branches:{}".format(n,w,branches))
       
        if os.path.exists('data/detwooram_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy'):
            sub_costs = np.load('data/detwooram_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy', allow_pickle=True)
        else:
            sub_costs = []
            for i in us_range:
                u = 2 ** i
                if u>n/4:
                    break
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
            np.save('data/detwooram_var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_nyc_spatial.npy', sub_costs)
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
    ws=[1,10,100,500,1000,10000]
    for u_order in [0]:
        u = 2 ** u_order
        print("u:{}".format(u))
        if os.path.exists('data/detwooram_var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy'):
            costs = np.load('data/detwooram_var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial_h.npy', allow_pickle=True)
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
            np.save('data/detwooram_var_w_results' + time_type + '_n' + str(n) + '_u' + str(u) + '_b' + str(
                branches) + '_nyc_spatial_h.npy', costs)
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
    n_orders=list(range(10,23,1))
    w=1
    for u_order in [0]:
        u = 2 ** u_order

        if False:#os.path.exists('data/detwooram_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy'):
            costs = np.load('data/detwooram_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy', allow_pickle=True)
        else:
            costs = []
            # 164,3440
            for n_order in n_orders:
                n=2**n_order

                server_storage_cost, client_storage_cost, res = runningcode.getLoadTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                costs.append([n_order, server_storage_cost, client_storage_cost, res])
            np.save('data/detwooram_var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_nyc_spatial.npy', costs)
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




def var_branches(threshold=2):
    branches_set = [8]
    print("Entering function: var_branches(), branches_set:", branches_set)
    n = 16384
    for branches in branches_set:
        print("get information for n:{},branches:{}".format(n,branches))
        # trend_w_occ()
       # collectRunningInfo_var_w(n, threshold=threshold, branches=branches, time_type='load')
       # collectRunningInfo_var_u(n, threshold=threshold, branches=branches,time_type='occ')
        collectRunningInfo_var_w(n, threshold=threshold, branches=branches,time_type='load')

    # for branches in branches_set:
    #     print("get information var n,branches:{}".format( branches))
    #     collectRunningInfo_var_n(threshold=threshold,branches=branches)



print("threshold = 2-------------------------")
var_branches(threshold=2)
#showAnalyticalOCCTime(8)
#showAnalyticalOCCTime_var_w()

detwooram_occ_costs_var_w=[0.005217359999999473, 0.05754428000000075, 0.6271611000000007, 3.112444899999996, 6.052638220000008, 36.79552953999999]
#[0.006600679999999102, 0.06869814000000246, 0.7826531999999929, 7.300129799999991, 41.39193636]
detwooram_load_costs_var_w=[]

#average bandwidth: [997.76, 11252.48, 123606.4, 584149.12, 1094844.16, 6185193.6]