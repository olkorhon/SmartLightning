from __future__ import print_function

from datetime import datetime

import pandas as pd
import numpy as np

from dbconfig import DB_CONFIG
from db_api import LightSenseDatabase

from bokeh_heatmap import makeHeatmap
from bokeh_network import makeNetwork

class Node(object):

    def __init__(self, location, data=None):
        self.pos_x = location["x"]
        self.pos_y = location["y"]
        self.temp_readings = None
        self.humidity_readings = None
        self.cycle_readings = None
        self.voltage_reading = None
        self.all_readings = pd.DataFrame(data, index=['Timestamp'], columns=["Temperature", "Humidity", "Cycle count", "Voltage"])

    def get_temperatures_by_time_window(self, start_time, end_time):
        return self.temp_readings.ix[start_time:end_time]
    
    def get_measurement_count_by_time_window(self, start_time, end_time):
        return self.temp_readings.ix[start_time:end_time].shape[0]
        
    def get_measurements_count_by_day(self):
        return self.temp_readings.groupby(pd.TimeGrouper(freq='D')).size()
        
    def get_measurements_count_by_hour(self):
        return self.temp_readings.groupby(pd.TimeGrouper(freq='H')).size()

    def get_measurements_count_by_15_min(self):
        return self.temp_readings.groupby(pd.TimeGrouper(freq='15Min')).size()
        
    def get_measurements_count_by_minute(self):
        return self.temp_readings.groupby(pd.TimeGrouper(freq='Min')).size()


def main():
    try:
        db = LightSenseDatabase(DB_CONFIG)
    except:
        main()
        return
        
    nodes = {}
    node_ids = set()

    # Fetch unique nodes
    for row in db.get_nodes():
        if row.node_id not in node_ids:
            node_ids.add(row.node_id)
            nodes[row.node_id] = Node(row.location)

    makeNetwork(nodes)

    # Fetch data to nodes
    for node_id in [250, 257, 259, 254, 253, 251, 252]:
        print ("Processing node:", str(node_id))
        temperature_readings = db.get_node_temperatures_by_node_id(node_id)
        nodes[node_id].temp_readings = pd.DataFrame.from_records(temperature_readings, index=['Timestamp'], exclude=['Measurement'])
        #print (nodes[node_id].temp_readings.tail())

    source_node_df = nodes[250].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    sink_node_df = nodes[257].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    print("From node 250 to node 257")
    calc_traffic_between_nodes(source_node_df, sink_node_df, 15)
    print("From node 257 to node 250")
    calc_traffic_between_nodes(sink_node_df, source_node_df, 15)

    source_node_df = nodes[259].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    sink_node_df = nodes[254].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    print("From node 259 to node 254")
    calc_traffic_between_nodes(source_node_df, sink_node_df, 15)
    print("From node 254 to node 259")
    calc_traffic_between_nodes(sink_node_df, source_node_df, 15)

    source_node_df = nodes[250].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    sink_node_df = nodes[253].get_temperatures_by_time_window(datetime(2016, 2, 15), datetime(2016, 2, 16))
    print("From node 250 to node 253")
    calc_traffic_between_nodes(source_node_df, sink_node_df, 15)
    print("From node 253 to node 250")
    calc_traffic_between_nodes(sink_node_df, source_node_df, 15)

    source_node_df = nodes[251].get_temperatures_by_time_window(datetime(2016, 1, 15), datetime(2016, 1, 16))
    sink_node_df = nodes[252].get_temperatures_by_time_window(datetime(2016, 1, 15), datetime(2016, 1, 16))
    print("From node 251 to node 252")
    calc_traffic_between_nodes(source_node_df, sink_node_df, 15)
    print("From node 252 to node 251")
    calc_traffic_between_nodes(sink_node_df, source_node_df, 15)

    # This is my jam brah
    #testLocation = {'x': 1337, 'y': 1337}
    #newTestNode = Node(testLocation)
    
    #temperature_readings = db.get_node_temperatures_by_node_id(250)
    #newTestNode.temp_readings = pd.DataFrame.from_records(temperature_readings, index=['Timestamp'], exclude=['Measurement'])
 
    #print(newTestNode.temp_readings)
    #print(newTestNode.get_temperatures_by_time_window('2016-01-01 00:00:00','2016-01-10 12:00:00'))
    #print(newTestNode.get_measurement_count_by_time_window('2016-01-01 00:00:00','2016-01-10 12:00:00'))
    #print(newTestNode.get_measurements_count_by_day())
    #print(newTestNode.get_measurements_count_by_hour())
    #print(newTestNode.get_measurements_count_by_15_min()) 
    #print(newTestNode.get_measurements_count_by_minute())

    #makeHeatmap(nodes)
    
def calc_traffic_between_nodes(source_node_df, sink_node_df, offset):
    # offset = excpected time in seconds that it takes to walk between nodes
    
    traffic_ctr = 0
    event_timestamps = []
    for timestamp in list(source_node_df.index):
        print(timestamp)
        # get timestamp of event
        # add 'timeframe' seconds to timestamp
        target = timestamp + pd.DateOffset(seconds=offset)
        # call sink_node.get_measurement_count_by_time_window()
        count = sink_node_df.ix[timestamp:target].shape[0]
        if (count > 1):
            event_timestamps.append(timestamp)
    df = pd.DataFrame(event_timestamps, index=event_timestamps)
    grouped_by_hour = df.groupby(pd.TimeGrouper(freq='H')).size()
    print(grouped_by_hour)
    print("\n")
    return traffic_ctr

if __name__ == "__main__":
    main()
