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
sPASD_OCC_var_u={500:[[1, 2, 4, 8, 16, 32, 64, 128],[0.005993914588000009, 0.005617065167999999, 0.005071719659999989, 0.005001000964000018, 0.004978863172000011, 0.00467026029200002, 0.00520211810400001, 0.005224565024000012]],
                 100:[[1, 2, 4, 8, 16, 32, 64, 128],[0.00593702982, 0.005905431880000003, 0.005729267299999969, 0.006040538960000009, 0.0062887059600000095, 0.006926122939999959, 0.008640243319999968, 0.010719192479999994]],
              1000:[[1, 2, 4, 8, 16, 32, 64, 128],[0.005876882586000011, 0.005500149002000034, 0.005045881222000016, 0.004902791372000038, 0.004558746856000007, 0.004057626267999967, 0.004173401393999984, 0.004046403806000035]]}
'''w=1000-31%'''
sPASD_Load_var_u={500:[[1, 2, 4, 8, 16, 32, 64, 128],[0.0060989415600002025, 0.005657660708000148, 0.005210164956000081, 0.005182827591999994, 0.004974888092000111, 0.004741388452000029, 0.0051078770719999375, 0.005388168084000099]
],                100:[[1, 2, 4, 8, 16, 32, 64, 128],[0.00598453561999986, 0.005803566080000292, 0.005644728700000269, 0.006076357479999933, 0.006562941260000116, 0.007049462479999602, 0.00900305279999975, 0.010779875900000116]
],                1000:[[1, 2, 4, 8, 16, 32, 64, 128],[0.006155239893999969, 0.005672687996000059, 0.005064586747999983, 0.004982311876000003, 0.004669026527999958, 0.004194563051999994, 0.004454402643999947, 0.004422890089999982]]
}

sPASD_OCC_var_w={1:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.004276851999999997, 0.05036864799999918, 0.546515986, 4.973174614, 8.943152085999989, 12.470192042000003, 15.493742758000012, 18.22123261399999, 20.51234180600004, 22.65717546000009, 24.51464299199997, 26.292628251999957, 27.939684902000046]],
                 32:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.0892131999999765, 0.16530265800000052, 0.6729001880001124, 3.8313710579999314, 6.596005501999843, 9.127098162000074, 11.18238535000015, 13.147845914000099, 14.813834494000002, 16.390067648000148, 17.820820622000028, 19.381571042000104, 20.65204990199978]]}#[0.08653082199999998, 0.17015839200000002, 0.6556927880000001, 3.7542444980000003, 6.5660345000000016, 8.908619461999999, 11.007055148000005, 12.828672409999994, 14.657770383999997, 16.058010187999997, 17.648336429999997, 18.927906708000002, 20.184585348]]}
# sPASD_Load_var_w={1:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.004215652000057162, 0.04809482799981197, 0.5551381519997812, 5.692824574000333, 11.397119443999909, 17.11746454200009, 22.807232151999923, 28.156031496000068, 33.81041601600016, 39.51076757599971, 45.247709428000164, 50.82130523199994, 56.541375642000276]],
#                  16:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],[0.04882844000021578, 0.12328288000004249, 0.6119958740002767, 4.4838381899998785, 8.435096434000297, 12.39400115400087, 16.336914940000135, 20.063722631999553, 24.847645737999702, 27.599774719999985, 32.15497171000025, 38.30813050400087, 39.60981358000019]],
#                  32:[[1, 10, 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000],]}
sPASD_Load_var_n={1:[[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,22],[0.00301668799995241, 0.0031982419999803825, 0.003552717999937158, 0.0039092439999512864, 0.004183838000044488, 0.004606131999971694, 0.005094407999986288, 0.005881490000010672, 0.005828086000037729, 0.007083271999945282, 0.007300608000041393, 0.008008398000165472, 0.007900956000084988]],
             32:[[10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,22],[0.001911471703999705, 0.002101534304000379, 0.0030465616000001318, 0.003885744144000055, 0.004433729591999727, 0.005466128343999735, 0.006190688348000112, 0.00697949792800122, 0.007687547352000838, 0.008179423064000439, 0.008475973063997808, 0.009162765904000553, 0.009523777779999947]]}
DetWoOTRAM_occ_var_w={1:[[1, 10, 100, 500, 1000, 10000],[0.004874720000000002, 0.05124666200000092, 0.5390649659999996, 2.60485549, 4.871239331999993, 27.776928226]#0.00520971
]} #(h+1)
DetWoOTRAM_load_var_w={1:[[1, 10, 100, 500, 1000, 10000],[0.002489366000002099, 0.026607920000001287, 0.3504389200000037, 2.0314496719999626, 4.4659235700000135, 52.910846381999974]
]} #(h)
def compareSchemes():
    plt.figure(figsize=(9, 4.5))
    colors = ['#254973', '#46BEA0', '#F55073', '#FFD76E']
    markers = ['^', '+', '*', 'h', '.-']
    tic = 0
    start, end = 1, 8
    schemes_name=['Path ORAM \n(recursive)','DetWoORAM', 'Baseline \n'+r'$s$PASD', r'$s$PASD']
    d_pathoram=7049.24
    w=1000
    d_detworam=DetWoOTRAM_load_var_w[1][1][4]
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
    plt.ylim((0,15000))
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
        plt.ylim((0.00, 0.012))
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
    plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
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
   # ax.yaxis.set_major_locator(ticker.MultipleLocator(0.005))
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

    plt.gca().ticklabel_format(axis='y', style='scientific', scilimits=(1.8, 4), useMathText=True)
   # ax.grid()

   # plt.ylim([0.01,0.135])
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
