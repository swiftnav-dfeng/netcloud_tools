from multiprocessing.sharedctypes import Value
import urllib
import requests
import datetime
import json
import urllib.parse

class Netcloud:
    ENDPOINTS = [
        'routers',
        'router_logs'
    ]
    API_URL = 'https://www.cradlepointecm.com/api/v2/'
    RESULT_LIMIT = 500

    def __init__(self, xcpapiid, xcpapikey, xecmapiid, xecmapikey):
        self.headers = {
            'X-CP-API-ID': xcpapiid,
            'X-CP-API-KEY': xcpapikey,
            'X-ECM-API-ID': xecmapiid,
            'X-ECM-API-KEY': xecmapikey,
            'Content-Type': 'application/json' 
        }
    
    def get_generic(self, endpoint:str, fields:dict):
        url  = self.API_URL + endpoint

        #query = '&'.join([(key + '=' + urllib.parse.urlencode(value)) for key, value in fields.items()])
        query = urllib.parse.urlencode(fields)
        endpoint += '/?' + query
        
        url = self.API_URL + endpoint

        resp = requests.get(url, headers=self.headers)
        
        return resp


    def get_group(self, group_name):
        endpoint = f'groups/?name={urllib.parse.quote(group_name)}'

        url = self.API_URL + endpoint

        resp = requests.get(url, headers=self.headers)

        return resp.text


    def get_router(self, **kwargs):
        endpoint = '/routers/'
        if kwargs is not None:
            query = '&'.join([(key + '=' + value) for key, value in kwargs.items()])
            endpoint += '?' + query

        url = self.API_URL + endpoint
        
        resp = requests.get(url, headers=self.headers)
        return resp.text

    def get_net_devices(self, **kwargs):
        endpoint = '/net_devices/'
        if kwargs is not None:
            query = '&'.join([(key + '=' + value) for key, value in kwargs.items()])
            endpoint += '?' + query

        url = self.API_URL + endpoint
        
        resp = requests.get(url, headers=self.headers)
        return resp.text


    def filter_netdevice_by_router(self, router, ignore_lan=True):
        endpoint = f'/net_devices/?router={router}'

        url = self.API_URL + endpoint

        devices = []
        while url:
            resp = requests.get(url, headers=self.headers)

            resp_json = json.loads(resp.text)
            #print(json.dumps(resp_json, indent=2))

            
            for device in resp_json['data']:
                if ignore_lan is True:
                    if device['name'] == 'ethernet-lan' or device["ipv4_address"] == "192.168.1.1":
                        continue
                devices.append(device['id'])
            

            url = resp_json['meta']['next']
        
        return devices

    # time format 2022-05-23T22:40:31.584039+00:00
    def usage_samples_30days(self, netdevice):
        today = datetime.date.today()
        #first_day = today - datetime.timedelta(days=30)

        endpoint = f'/net_device_usage_samples/?net_device={netdevice}'
        endpoint += f'&created_at__lt={today}&created_at__gt={today - datetime.timedelta(days=30)}&limit={self.RESULT_LIMIT}'

        url = self.API_URL + endpoint
    
        bytes_in = 0
        bytes_out = 0
        
        while url:
            resp = requests.get(url, headers=self.headers)

            try:
                resp_json = json.loads(resp.text)
            except Exception as e:
                print(resp.text)

            
            for sample in resp_json['data']:
                bytes_in += int(sample['bytes_in'])
                bytes_out += int(sample['bytes_out'])
            

            url = resp_json['meta']['next']

        return bytes_in, bytes_out

    def get_router_logs(self, router:str, **kwargs):
        endpoint = f'/router_logs/'
        fields = {
            'router': str(router),
            **kwargs
        }

        log_entries = []

        resp = self.get_generic(endpoint, fields)
        
        while True:
            resp.raise_for_status()
        
            resp_json = json.loads(resp.text)
            print(json.dumps(resp_json, indent=2))

            for entry in resp_json:
                log_entries.append(entry)
            
            url = resp_json['meta']['next']

            if url is None:
                break

            resp = requests.get(url, headers=self.headers)

        return log_entries
        