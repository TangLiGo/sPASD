import os
from math import log
import time
import os
import matplotlib.ticker as ticker
from math import log
import time
from runningcode_nyc_spatial import getLoadTime,getOCCTime,getAnalyticalLoad,getAnalyticalOCC,getAnalyticalLoadTime,getAnalyticalOCCTime

import matplotlib.pyplot as plt
from random import randint
import random
import math
import numpy as np
import scipy.stats as ss
import scipy.optimize as optimize
sPASD_OCC_var_u={500:[[1, 2, 4, 8, 16, 32, 64, 128],[0.005263911988000001, 0.004858210895999995, 0.004506688468, 0.004304764687999991, 0.004264435236000009, 0.004076894672000012, 0.004413965615999991, 0.004574276808000036]],
                 100:[[1, 2, 4, 8, 16, 32, 64, 128],[0.005382188319999886, 0.005206003800000098, 0.005273784279999927, 0.0054655811600001466, 0.006111774819999982, 0.006406526919999851, 0.008209055419999868, 0.009604994239999769]],
                 1000:[[1, 2, 4, 8, 16, 32, 64, 128],[0.0049177606940000165, 0.0045646649560000105, 0.004150046798000021, 0.003942970011999969, 0.0038024427620000282, 0.0034943895780000004, 0.003608070076000031, 0.0036023717719999965]]}
sPASD_Load_var_u={500:[[1, 2, 4, 8, 16, 32, 64, 128],[0.005618410007999992, 0.005236427660000027, 0.0048635672599999635, 0.00485163163999985, 0.0048144465839999795, 0.004456067367999858, 0.005186073823999831, 0.0055831560600001105]
],                100:[[1, 2, 4, 8, 16, 32, 64, 128],[0.0055206198399999264, 0.0053507771399996275, 0.005466835199999513, 0.005656000379999751, 0.006166063319999922, 0.006449929520000114, 0.008335940379999192, 0.00985518407999989]
],                1000:[[1, 2, 4, 8, 16, 32, 64, 128],[0.0056888706620001174, 0.005278064273999989, 0.004798739864000091, 0.004666129552000002, 0.004319260830000003, 0.004050948410000001, 0.0044034038739999785, 0.004517087547999999]]
}

sPASD_OCC_var_w={1:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.004276851999999997, 0.05036864799999918, 0.546515986, 4.973174614, 8.943152085999989, 12.470192042000003, 15.493742758000012, 18.22123261399999, 20.51234180600004, 22.65717546000009, 24.51464299199997, 26.292628251999957, 27.939684902000046]],
                 16:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.048444190000009255, 0.1271987939999599, 0.5898845440000877, 3.7652544739998484, 6.44757301600006, 8.636095623999973, 10.628761248000227, 12.437489895999825, 14.041063484000006, 15.519459792000088, 16.462161282000125, 17.80872034399996, 18.577525631999926]],
                 32:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.08933092400000532, 0.1719438259999697, 0.6624589700000252, 3.5447752359999867, 5.8670074579998985, 8.060276439999962, 9.617588473999895, 10.957623770000064, 12.368766585999946, 13.259157934000031, 14.429270045999948, 15.464985775999958, 16.346373356000186]]}

sPASD_Load_var_w={1:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.004215652000057162, 0.04809482799981197, 0.5551381519997812, 5.692824574000333, 11.397119443999909, 17.11746454200009, 22.807232151999923, 28.156031496000068, 33.81041601600016, 39.51076757599971, 45.247709428000164, 50.82130523199994, 56.541375642000276]],
                 16:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.04882844000021578, 0.12328288000004249, 0.6119958740002767, 4.4838381899998785, 8.435096434000297, 12.39400115400087, 16.336914940000135, 20.063722631999553, 24.847645737999702, 27.599774719999985, 32.15497171000025, 38.30813050400087, 39.60981358000019]],
                 32:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],]}
sPASD_Load_var_n={1:[[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],[0.003103718, 0.003372852000000001, 0.0036244820000000005, 0.004038114000000001, 0.004541943999999999, 0.005112266, 0.005134945999999999, 0.006415768000000001, 0.006233333999999999, 0.007333674000000001, 0.007273617999999999, 0.007679456, 0.008701020000000002]
],               32: [[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                       [1.7451130520000004, 1.9770189360000001, 2.8492937339999997, 3.554889123999999, 4.0472696779999975, 4.903318457999998, 5.7365724479999995, 6.334785116000001, 7.091342540000002, 7.7736109199999985, 8.157956833999998, 8.537855235999997, 8.948859756000004]
]}
sPASD_OCC_var_n=dict()
DetWoOTRAM_occ_var_w={1:[[1, 10, 100, 500, 1000, 10000],[0.00556603000006362, 0.06188922000003003, 0.6944156400000066, 3.265697032000044, 6.128235314000012, 34.708415837999965]]}
DetWoOTRAM_load_var_w={1:[[1, 10, 100, 500, 1000, 10000],[0.005510661999999999, 0.06438453199999969, 0.712170514, 3.592402736000003, 7.18158022600001, 72.94106659]]} #(h)
def compareSchemes():
    plt.figure(figsize=(9, 4.5))
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E']
    markers = ['^', '+', '*', 'h', '.-']
    tic = 0
    start, end = 1, 8
    schemes_name=['Path ORAM \n(recursive)','DetWoORAM', 'Baseline \n'+r'$s$PASD', r'$s$PASD']
    d_pathoram=14049.24
    w=1000
    d_detworam=DetWoOTRAM_load_var_w[1][1][4]#7.029188436#
    d_baseline=sPASD_OCC_var_u[w][1][0]*w
    d_spasd=sPASD_OCC_var_u[w][1][5]*w
    schemes_time=[d_pathoram,d_detworam,d_baseline,d_spasd]
    print("schemes_time",schemes_time)
    plt.bar(schemes_name, schemes_time,width=0.4)
    scheme_num=4
    x=np.arange(scheme_num)
    width=0.4

    plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
    tic += 1
    for a,b in zip(x,schemes_time):
        plt.text(a,b*1.01,'%.2f'% b, ha='center',va='bottom',fontsize=18)
  #  plt.xlabel(r'$u$', fontsize=22)
    plt.ylabel('CPU Time (sec)', fontsize=18)
    plt.gca().yaxis.get_offset_text().set_fontsize(18)
  #  plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(0.01))
   # tickes = [r'$2^{0}$', r'$2^{1}$', r'$2^{2}$', r'$2^{3}$', r'$2^{4}$', r'$2^{5}$', r'$2^{6}$', r'$2^{7}$']
  #  plt.xticks(list(range(8))[start:end], tickes[start:end], fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.yscale('log')
    plt.ylim((0,35000))
    #  plt.title(name)
   # plt.legend(fontsize=22)
    plt.grid(axis="y")
    plt.savefig('results/CompareSchemes.pdf', bbox_inches='tight')
def drawReal_vs_Analytical(branching,time_type='occ'):
    fig=plt.figure(figsize=(15,4))
    colors_real = ['#254973', 'dimgray','rosybrown']
    markers_real = ['^', '>', 's']
    colors_theo = [ '#46BEA0',  '#F55073','seagreen']
    markers_theo = ['*',  '+', 'o']
    start, end = 1, 8
    costs = []
    n = 16384
    start, end = 1, 8
    ws=[100,500,1000]
    node_process_time=0.0015
    tic=0
    for w in ws:#list(range(64, 700, 128)):
        if time_type=='occ':
            sPASD_time=sPASD_OCC_var_u[w]
        elif time_type=='load':
            sPASD_time=sPASD_Load_var_u[w]
        us_range=sPASD_time[0]
        Analytical_time=[]
        for u in us_range:
            if time_type=='occ':
                Analytical_time.append(node_process_time*getAnalyticalOCCTime(n, u, w, branching=branching) / w)
            else:
                Analytical_time.append(node_process_time*getAnalyticalLoadTime(n, u, w, branching=branching) / w)
        ax = plt.subplot(1, 3, tic + 1)
        plt.plot([log(u,2) for u in us_range[start:end]], Analytical_time[start:end], color=colors_theo[0], marker=markers_theo[0],
                 label=r'Analytical')

        plt.plot([log(u,2) for u in us_range[start:end]], sPASD_time[1][start:end], color=colors_real[0], marker=markers_real[0],
                 label=r'Real')
        plt.xlabel(r'$u$ ($w=$' + str(w) + ')', fontsize=22)
        if tic == 0:
            plt.ylabel('CPU Time (sec)', fontsize=22)
            plt.gca().yaxis.get_offset_text().set_fontsize(22)
            plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
            plt.yticks(fontsize=22)
        else:
            ax.set_yticklabels([])
        tic += 1
        tickes = [r'$2^{0}$', r'$2^{1}$', r'$2^{2}$', r'$2^{3}$', r'$2^{4}$', r'$2^{5}$', r'$2^{6}$', r'$2^{7}$']
        plt.xticks(list(range(8))[start:end], tickes[start:end],
                   fontsize=22)
        plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(0.002))
        plt.xticks(fontsize=22)
        # plt.xlabel(fontsize=22)
        plt.ylim((0.00, 0.01))
        # plt.yscale('log')
        plt.legend(fontsize=22)
        plt.grid()
    plt.subplots_adjust(wspace=0.05, hspace=0)
    plt.savefig('results/Real_vs_Analytical_'+time_type+'.pdf', bbox_inches='tight')
    plt.show()



def drawW(time_type='occ'):
    fig=plt.figure(figsize=(6,5))
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E','#254973', '#46BEA0', '#F55073', '#FFD76E']
    markers = ['^', '+', '*', 'h', 'p','p','*', 'h', '+']

    tic = 0
    start,end=2,13

    us_labels=[r'$2^{0}}$',r'$2^{0}}$',r'$2^{0}}$']
    us_range=[32]

    for u in us_range:
        if time_type=='occ':
            ws,times=sPASD_OCC_var_w[u][0],sPASD_OCC_var_w[u][1]
        elif time_type=='load':
            ws,times=sPASD_Load_var_w[u][0],sPASD_Load_var_w[u][1]
    print("ws[start:2:end]", ws[start:end:2])
    plt.plot(ws[start:],times[start:], color=colors[tic],
                 marker=markers[tic],label='$s$PASD')
    tickes = [r'$1$', r'$10$', r'$10^{2}$', r'$10^{3}$', r'$2\times10^{3}$', r'$3\times10^{3}$', r'$4\times10^{3}$', r'$5\times10^{3}$', r'$6\times10^{3}$', r'$7\times10^{3}$', r'$8\times10^{3}$', r'$9\times10^{3}$', r'$10^{4}$']
    # plt.xticks(ws[start::3], tickes[start::3],
    #                fontsize=22)
    tic+=1



   # ax=plt.gca()
  #  plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
    plt.gca().ticklabel_format(axis='x', style='scientific', scilimits=(1.8, 4), useMathText=True)
   # ax.grid()

   # plt.ylim([0.01,0.135])
   # plt.yscale('logit')
    plt.tick_params(labelsize=22)
    plt.xlabel(r'$w$', fontsize=22)
    plt.ylabel('CPU Time (sec)', fontsize=22)
    # plt.xticks(ws,[r'$10^{0}$', r'$10^{1}$', r'$10^{2}$', r'$10^{3}$', r'$10^{4}$'],
    #         fontsize=22)
   # plt.xlim((-0.008, 0.11))
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(2000))
   # plt.gca().yaxis.get_offset_text().set_fontsize(20)
  #  plt.gca().xaxis.get_offset_text().set_fontsize(20)
    plt.xticks(fontsize=22)
    plt.gca().xaxis.get_offset_text().set_fontsize(22)
    plt.gca().yaxis.get_offset_text().set_fontsize(22)
    plt.yticks(fontsize=22)

  #  plt.title(name)
 #   plt.legend(fontsize=22)
    plt.gca().grid()
   # plt.legend(fontsize=22)
    plt.savefig('results/time_var_w_'+time_type+'.pdf', bbox_inches='tight')
    plt.show()
def drawN(time_type='occ'):
    fig=plt.figure(figsize=(6,5))
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E','#254973', '#46BEA0', '#F55073', '#FFD76E']
    markers = ['^', '+', '*', 'h', 'p','p','*', 'h', '+']

    tic = 0


    tickes=[r'$2^{10}}$',r'$2^{11}}$',r'$2^{12}}$',r'$2^{13}}$',r'$2^{14}}$',r'$2^{15}}$',r'$2^{16}}$',r'$2^{17}}$',r'$2^{18}}$',r'$2^{19}}$',r'$2^{20}}$',r'$2^{21}}$',r'$2^{22}}$']

    us_range=[32]
    for u in us_range:
        if time_type=='occ':
            ns,times=sPASD_Load_var_n[u][0],sPASD_Load_var_n[u][1]
        elif time_type=='load':
            ns,times=sPASD_Load_var_n[u][0],sPASD_Load_var_n[u][1]
        plt.plot(ns, times, color=colors[tic],
                 marker=markers[tic])
        plt.xticks(ns[::2], tickes[::2],fontsize=22)
        tic+=1



   # ax=plt.gca()
   # plt.gca().ticklabel_format(axis='x', style='scientific', useMathText=True)

  #  plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
   # ax.grid()

    plt.ylim([1,10.3])
   # plt.yscale('logit')
    plt.tick_params(labelsize=22)
    plt.xlabel(r'$N$', fontsize=22)
    plt.ylabel('CPU Time (sec)', fontsize=22)
    # plt.xticks(ws,[r'$10^{-3}$', r'', r'$5\times 10^{-2}$', r'$10^{-1}$'],
    #        fontsize=22)
   # plt.xlim((-0.008, 0.11))
   # ax.yaxis.set_major_locator(ticker.MultipleLocator(0.005))
   # plt.gca().yaxis.get_offset_text().set_fontsize(20)
  #  plt.gca().xaxis.get_offset_text().set_fontsize(20)
    plt.xticks(fontsize=22)

    plt.gca().yaxis.get_offset_text().set_fontsize(22)
    plt.yticks(fontsize=22)

  #  plt.title(name)
 #   plt.legend(fontsize=22)
    plt.gca().grid()
   # plt.legend(fontsize=22)
    plt.savefig('results/time_var_N_'+time_type+'.pdf', bbox_inches='tight')
    plt.show()



compareSchemes()
drawN()
drawW('occ')
#drawW(time_type='load')
drawReal_vs_Analytical(8)
drawReal_vs_Analytical(8,time_type='load')
