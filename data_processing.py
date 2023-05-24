import numpy as np
import pandas as pd
from pandas.core import resample as rp
import math
import seaborn as sns
import matplotlib.pyplot as plt
import os
min_lon,max_lon,min_lat,max_lat=-74.2572,-73.6992,40.4960,40.9156
dict_partition2grid={0:{1024:3600,16384:435600},1:{1024:7056,16384:828100},2:{1024:10000,4096:108900,16384:1071225, 65536:11943936}}
#dict_partition2grid={1024:3600,16384:234360}
def parse_date(date_string):
    #print("date_string",date_string)
    return pd.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

def read_dataset(dataset_path="/Users/tangnvshi/Downloads/nyc-taxi-trip-duration/data.csv"):
    df = pd.read_csv(dataset_path, header=0, usecols=["pickup_datetime",
                                                                                   "dropoff_datetime",
                                                                                   "pickup_longitude",
                                                                                   "pickup_latitude",
                                                                                   "dropoff_longitude",
                                                                                   "dropoff_latitude"],
                     parse_dates=["pickup_datetime", "dropoff_datetime"],
                     date_parser=parse_date, nrows=1048575,
                     dtype={"pickup_longitude": "float64", "pickup_latitude": "float64", "dropoff_longitude": "float64",
                            "dropoff_latitude": "float64"})
    df.sort_values(by='pickup_datetime', inplace=True)
    #print("fdafd",df.head())
    return df


def remove_invalid_rows(df):
    #remove_rows_that_contain_0_values
    return df[(df['pickup_longitude'] != float(0)) & (df['pickup_latitude'] != float(0)) &
              (df['dropoff_longitude'] != float(0)) & (df['dropoff_latitude'] != float(0))]

def impose_boundary(df):
    return df[(df['pickup_longitude'] <= max_lon) & (df['pickup_longitude'] >= min_lon) &
              (df['pickup_latitude'] >= min_lat) & (df['pickup_latitude'] <= max_lat)]
    # return df[(df['pickup_longitude'] <= float(-73.6992)) & (df['pickup_longitude'] >= float(-74.2572)) &
    #           (df['pickup_latitude'] >= float(40.4960)) & (df['pickup_latitude'] <= float(40.9156)) &
    #           (df['dropoff_longitude'] <= float(-73.6992)) & (df['dropoff_longitude'] >= float(-74.2572)) &
    #           (df['dropoff_latitude'] >= float(40.4960)) & (df['dropoff_latitude'] <= float(40.9156))]
    #[-74.7,-73.4];[40.25,41.25]

def map_point_to_grid(df,grids_num=1024):
    grids_lat_num=grids_lon_num=math.sqrt(grids_num)
    lon_interval=(max_lon-min_lon)/grids_lon_num
    lat_interval=(max_lat-min_lat)/grids_lat_num
   # print("lon_interval:{},lat_interval:{}".format(lon_interval,lat_interval))
   # print(df[['pickup_longitude','pickup_latitude']].head())
    df['pickup_gridID']=df.apply(lambda x:(x['pickup_longitude']-min_lon)//lon_interval+grids_lon_num*((x['pickup_latitude']-min_lat)//lat_interval),axis=1)
   # print(df[['pickup_longitude','pickup_latitude','pickup_gridID']].head())
    df['pickup_gridID']=df['pickup_gridID'].astype(int)
    return df

def show_request_distribution(df):
    fig=df['pickup_gridID'].plot.hist(bins=30).get_figure()
    fig.savefig('request_distribution_all.pdf')
def show_request_num_distribution(df, time_slot='30Min'):
    df = df.set_index('pickup_datetime')
    df_slots = df.groupby(rp.TimeGrouper(time_slot))
    #group num:df_slots.ngroups, group sizes:df_slots.size()
   # fig = df_slots.size().plot(kin='bar').get_figure()

    #df_slots.size().to_csv("data/slots_sizes.csv")
    slots_sizes=df_slots.size()
    print("time_slot:{}, request number mean:{}, std:{}, max:{}, min:{}".format(time_slot,slots_sizes.mean(),slots_sizes.std(),slots_sizes.max(),slots_sizes.min()))

  #  fig=sns.barplot(x=group_sizes.index, y=group_sizes.values).get_figure()
    fig=df_slots.size().plot.hist(bins=30).get_figure()
    fig.savefig('request_num_distribution_time_slot_'+time_slot+'.pdf')
    # print("Group number:{}".format(df_slots.ngroups))
    # print("Group sizes:{}".format(df_slots.size()))
def analyze_requests_distribution(partition_num=1024,time_slot='10Min'):
    df = preprocessing(partition_num)
    show_request_distribution(df)
    show_request_num_distribution(df,time_slot=time_slot)
def get_unaccessed_area(df):
    df_grids = df.groupby('pickup_gridID')
    print("There are :{} grids are accessed:".format(df_grids.ngroups))
    #group num:df_slots.ngroups, group sizes:df_slots.size()


def collect_requests(df, req_num=196):
    overall_num = df.shape[0]
    set_num=overall_num//req_num
    req_sets=np.zeros([set_num,req_num])
    set_id=0
    while set_id<set_num:
        req_sets[set_id]=df[req_num*set_id:req_num*(set_id+1)]['pickup_gridID']#.to_numpy()
        set_id+=1
        #print("type",type(req_sets[set_id]),type(req_sets[set_id][0]))
    return req_sets

def select_data_slot(df,start_time='9:00',end_time='22:00'):
    if start_time=='0:00' and end_time=='23:59':
        return df
    return df.between_time(start_time,end_time)

def divide_data_by_day(df):

    df['day']=df['pickup_datetime'].dt.to_period('D')
    date_sets=df['day'].unique()
    #get gridID request number
    #df['pickup_gridID'].value_counts()
    fig=df['pickup_gridID'].plot.hist(bins=30).get_figure()
    fig.savefig('request_distribution.pdf')
    return df, date_sets

def analyze_each_day(df,date_sets,time_slot='1h'):
    for date_info in date_sets:
        # get one day info
        df_day = df[(df['day'] == date_info)]
        print("Date:{}, request number:{}".format(date_info, df_day.shape[0]))
        df_day = df_day.set_index('pickup_datetime')
        df_slots = df_day.groupby(rp.TimeGrouper(time_slot))
        print("Group number:{}".format(df_slots.ngroups))
        print("Group sizes:{}".format(df_slots.size()))

        for slot in df_slots:
            key, val = slot[0], slot[1]
         #   print("time slot:{}".format(key))
        #    print("requests:{}".format(val))

        break
# def preprocessing_copy(partition_num=1024):
#     print("Read dataset")
#     grids_num=dict_partition2grid[partition_num]
#     dataset_path="data/dataset_grids_num"+str(grids_num)+".npy"
#     if os.path.exists(dataset_path):
#         return pd.read_csv(dataset_path)
#     else:
#         df = read_dataset()
#         print("Remove 0 value rows")
#         df = remove_invalid_rows(df)
#         print("After removing 0 value rows: %s" % len(df))
#         print("Impose boundary")
#         df = impose_boundary(df)
#         print("After imposing boundary: %s" % len(df))
#         print("Map point to grid")
#         df = map_point_to_grid(df, grids_num=partition_num)
#         df.to_csv(dataset_path,header=True)
#     return df
def remove_remote_grids(df,threshold=2):
    value_counts=df['pickup_gridID'].value_counts()
    great_values=value_counts[value_counts>threshold].index
    return df[df['pickup_gridID'].isin(great_values)]
def preprocessing(grids_num=1024,threshold=2):
    print("Read dataset")
    df = read_dataset()
    print("Remove 0 value rows")
    df = remove_invalid_rows(df)
    print("After removing 0 value rows: %s" % len(df))
    print("Impose boundary")
    df = impose_boundary(df)
    print("After imposing boundary: %s" % len(df))
    print("Map point to grid")
    df = map_point_to_grid(df, grids_num=grids_num)
    df = remove_remote_grids(df,threshold=threshold)
    print("After removing remote grids: %s" % len(df))
    return df

def get_accessible_grids_ID(df):
    gridID_sets = df['pickup_gridID'].unique()
  #  print("type(gridID_sets)",type(gridID_sets))
 #   print("(gridID_sets)", (gridID_sets))
    print("accessible grids number",gridID_sets.shape)
    return gridID_sets
def get_requests_set(partition_num=1024,threshold=2,req_num=196,start_time='0:00',end_time='23:59'):
    grids_num=dict_partition2grid[threshold][partition_num]
   # grids_num=828100
    accessible_grids_ID_path="data/accessible_grids_ID_grids_num"+str(grids_num)+"_threshold_"+str(threshold)+".npy"
    #get requests
    requests_path="data/requests_grids_num"+str(grids_num)+"_request_num"+str(req_num)+"_allday_threshold_"+str(threshold)+".npy"
    #get requests
    if os.path.exists(requests_path) and os.path.exists(accessible_grids_ID_path):
        return np.load(requests_path,allow_pickle=True), np.load(accessible_grids_ID_path,allow_pickle=True)
    else:
        df = preprocessing(grids_num,threshold=threshold)
        accessible_grids_ID = get_accessible_grids_ID(df)
        np.save(accessible_grids_ID_path, accessible_grids_ID)
        df = select_data_slot(df, start_time=start_time, end_time=end_time)
        req_sets = collect_requests(df, req_num=req_num)
        np.save(requests_path,req_sets)

        return req_sets,accessible_grids_ID
def observe_spatial_distribution(partition_num=1024):
    df = preprocessing(partition_num)
    plt.scatter(df['pickup_longitude'], df['pickup_latitude'])
    plt.show()

def get_requests_set_gen(partition_num=1024,threshold=2,req_num=196,start_time='0:00',end_time='23:59'):
    grids_num=384199200
   # grids_num=828100 300000->7453 400000->8899
    #65536 6427350->47124 12250000->66334 11943936->65449 11957764->65442 11964681->65537
    #262144  96049800->123513 384199200->71828
    accessible_grids_ID_path="data/accessible_grids_ID_grids_num"+str(grids_num)+"_threshold_"+str(threshold)+".npy"
    #get requests
    requests_path="data/requests_grids_num"+str(grids_num)+"_request_num"+str(req_num)+"_allday_threshold_"+str(threshold)+".npy"
    #get requests
    if os.path.exists(requests_path) and os.path.exists(accessible_grids_ID_path):
        return np.load(requests_path,allow_pickle=True), np.load(accessible_grids_ID_path,allow_pickle=True)
    else:
        df = preprocessing(grids_num,threshold=threshold)
        accessible_grids_ID = get_accessible_grids_ID(df)
      #  np.save(accessible_grids_ID_path, accessible_grids_ID)
        df = select_data_slot(df, start_time=start_time, end_time=end_time)
        req_sets = collect_requests(df, req_num=req_num)
       # np.save(requests_path,req_sets)

        return req_sets,accessible_grids_ID
#get_requests_set()
#get_requests_set_gen()
#time_slot:30Min, request number mean:120.00354853479854, std:55.59877825188192, max:249, min:0
#time_slot:1h, request number mean:240.00709706959708, std:109.101057326991, max:461, min:0
#time_slot:10Min, request number mean:40.00118284493284, std:19.28331759229404, max:97, min:0
#get_requests_set()