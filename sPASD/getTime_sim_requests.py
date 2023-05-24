from runningcode import getLoadTime,getOCCTime,getAnalyticalLoad,getAnalyticalOCC,getAnalyticalLoadTime,getAnalyticalOCCTime
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
repeatTimes = 20
def collectRunningInfo_var_u(n,threshold,branches,time_type='occ'):
    print("Entering function: collectRunningInfo_var_u(n:{},dataset_th:{},branches:{},time_type:{})".format(n,threshold,branches,time_type))
    costs = []
    plt.figure()
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E', ]
    markers = ['^', '+', '*', 'h', '.-']
    xticks_set=[r'$2^{0}$',r'$2^{1}$', r'$2^{2}$', r'$2^{3}$', r'$2^{4}$', r'$2^{5}$', r'$2^{6}$',r'$2^{7}$']
    tic = 0
    start,end=0,8
    us_range=list(range(8))#[2**i for i in range(8)]
    w_props=[0.05,0.01,0.1,0.001]

    for w_prop in w_props:#list(range(64, 700, 128)):
        print("processing n:{}, w_prop:{}, branches:{}".format(n,w_prop,branches))
        w=int(w_prop*n)
        if os.path.exists('data/var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_sim.npy'):
            sub_costs = np.load('data/var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_sim.npy', allow_pickle=True)
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
            np.save('data/var_u_results'+time_type+'_n'+str(n)+'_w' + str(w) + '_b'+str(branches)+'_sim.npy', sub_costs)
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
        plt.plot(us_range[start:end], [u for u in time_records[start:end]], color=colors[tic],
                 marker=markers[tic],
                 label=r'$proportion$=' + str(w_prop))
       # costs.append([n, w, sub_costs])
       #  plt.plot(us_range[start:end], [u[0] for u in time_records[start:end]], color=colors[tic],
       #           marker=markers[tic],
       #           label=r'$proportion$=' + str(w_prop))
        tic += 1
    plt.xlabel(r'$u$', fontsize=20)
    plt.ylabel('CPU Time', fontsize=20)
    plt.ticklabel_format(style='sci', scilimits=(-2, -1), axis='y')
    plt.gca().yaxis.get_offset_text().set_fontsize(20)
    plt.xticks(us_range[start:end], xticks_set[start:end],
               fontsize=20)
    #  plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.legend(fontsize=20)
    fig_name='results/sPASD_var_u_'+time_type+'_n'+str(n)+'.pdf'
    plt.savefig(fig_name, bbox_inches='tight')
    #plt.show()
def collectRunningInfo_var_w(n,threshold,branches,time_type='occ'):
    print(
        "Entering function: collectRunningInfo_var_w(n:{},dataset_th:{},branches:{},time_type:{})".format(n, threshold,
                                                                                                          branches,
                                                                                                          time_type))

    plt.figure()
    w_props=[0.001, 0.01, 0.05, 0.1]
    for u_order in [0,2,4,6]:
        u = 2 ** u_order
        print("u:{}".format(u))
        if False:#os.path.exists('data/var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_sim.npy'):
            costs = np.load('data/var_w_results'+time_type+'_n'+str(n)+'_u' + str(u) + '_b'+str(branches)+'_sim.npy', allow_pickle=True)
        else:
            costs = []
            # 164,3440
            for w_prop in w_props:
                # n=2**n_order
                w = int(w_prop * n)
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
            np.save('data/var_w_results' + time_type + '_n' + str(n) + '_u' + str(u) + '_b' + str(
                branches) + '_sim.npy', costs)
        time_records=[costs[i][3].mean(axis=0)[0]/costs[i][0] for i in range(len(w_props))]
        print("u:{}; w range:{}".format(u,[costs[i][0] for i in range(len(w_props))]) )
        print("average time cost (per w):",time_records)
        results=[costs[i][3].mean(axis=0) for i in range(len(w_props))]

        results=[sub_costs[i][3].mean(axis=0) for i in range(len(sub_costs))]

        print("average requests:{}".format([result[1] for result in results]))
        print("data acces:{}".format([result[2] for result in results]))
        print("data_block_byte:{}".format([result[3] for result in results]))
        print("pos access:{}".format([result[4] for result in results]))
        print("pos_block_byte:{}".format([result[5] for result in results]))
        print("average bandwidth:", [result[2]*result[3]+result[4]*result[5] for result in results])
        print("server storage cost:{}, client storage cost:{}".format([sub_costs[i][1] for i in range(len(sub_costs))],[sub_costs[i][2] for i in range(len(sub_costs))]))

    #  plt.plot([c[1] for c in costs])

    #
    # plt.xlabel(r'$u$', fontsize=20)
    # plt.ylabel('CPU Time', fontsize=20)
    # plt.xticks(fontsize=20)
    # plt.yticks(fontsize=20)
    # plt.legend()
    # plt.savefig('results/detworam_t_vs_n.pdf', bbox_inches='tight')
def collectRunningInfo_var_n(threshold,branches):
    print(
        "Entering function: collectRunningInfo_var_n(dataset_th:{},branches:{}".format( threshold,
                                                                                                          branches))

    plt.figure()
    n_orders=list(range(11,21,3))
    w=1
    for u_order in [0,5]:
        u = 2 ** u_order

        if False:#os.path.exists('data/var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_sim.npy'):
            costs = np.load('data/var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_sim.npy', allow_pickle=True)
        else:
            costs = []
            # 164,3440
            for n_order in n_orders:
                n=2**n_order

                server_storage_cost, client_storage_cost, res = getLoadTime(n, u, w, threshold=threshold,
                                                                                repeatTimes=repeatTimes,
                                                                                branches=branches)
                costs.append([n_order, server_storage_cost, client_storage_cost, res])
                print("time for n_order:{} is:{}, all info:{}".format(n_order,res.mean(axis=0)[0],res.mean(axis=0)))
            np.save('data/var_n_results'+'_u' + str(u) + '_b'+str(branches)+'_sim.npy', costs)
        time_records=[costs[i][3].mean(axis=0)[0] for i in range(len(costs))]
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

    #  plt.plot([c[1] for c in costs])

    #
    # plt.xlabel(r'$u$', fontsize=20)
    # plt.ylabel('CPU Time', fontsize=20)
    # plt.xticks(fontsize=20)
    # plt.yticks(fontsize=20)
    # plt.legend()
    # plt.savefig('results/detworam_t_vs_n.pdf', bbox_inches='tight')

def showAnalyticalOCCTime(branching):
    costs = []
    n = 16384
    plt.figure()
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E']
    markers = ['^', '+', '*', 'h', '.-']
    tic = 0

    us_range=list(range(8))#[2**i for i in range(8)]
    w_props=[0.05,0.01,0.1]

    for w_prop in w_props:#list(range(64, 700, 128)):
        sub_costs=[]
        w=int(w_prop*n)
        for i in us_range:
            u = 2 ** i
            temp = getAnalyticalOCCTime(n, u, w, branching=branching) / w
            sub_costs.append([u, temp])
        print("w_prop={}, analytical occ time:{}".format(w,sub_costs))
        costs.append([n, w, sub_costs])
        plt.plot(us_range, [u for u in sub_costs], color=colors[tic], marker=markers[tic],
                 label=r'$w$=' + str(w))
        tic += 1
    plt.xlabel(r'$u$', fontsize=20)
    plt.ylabel('CPU Time', fontsize=20)
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.legend()
    plt.savefig('results/analytical_occTime_n'+str(n)+'.pdf', bbox_inches='tight')
    #plt.show()

def var_branches(threshold=2):
    branches_set = [8, 2]
    print("Entering function: var_branches(), branches_set:", branches_set)
    n = 16384
    # for branches in branches_set:
    #     print("get information for n:{},branches:{}".format(n,branches))
    #     # trend_w_occ()
    #     collectRunningInfo_var_u(n, threshold=threshold,branches=branches,time_type='occ')
    #     collectRunningInfo_var_u(n, threshold=threshold,branches=branches,time_type='load')
    for branches in branches_set:
        print("get information var n,branches:{}".format( branches))
        collectRunningInfo_var_n(threshold=threshold,branches=branches)



print("threshold = 2-------------------------")
var_branches(threshold=2)


