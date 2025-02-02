#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

from .config import Config
from .group import Vmess, Vless, Socks, SS, Mtproto, Trojan
from .selector import ClientSelector

class ClientWriter:
    def __init__(self, group, client_index):
        self.config_factory = Config()
        with open(self.config_factory.get_path('config_path'), 'r') as json_file:
            self.config = json.load(json_file)
        
        self.write_path = self.config_factory.get_path("write_client_path")
        self.template_path = self.config_factory.json_path
        self.group = group
        self.client_index = client_index
        self.node = group.node_list[client_index]

    def load_template(self, template_name):
        '''
        load special template
        '''
        with open(self.template_path + "/" + template_name, 'r') as stream_file:
            template = json.load(stream_file)
        return template

    def transform(self):
        user_json = None
        if type(self.node) == Vmess:
            self.client_config = self.load_template('client.json')
            user_json = self.client_config["outbounds"][0]["settings"]["vnext"][0]
            user_json["users"][0]["id"] = self.node.password
            user_json["users"][0]["alterId"] = self.node.alter_id

        elif type(self.node) == Vless:
            self.client_config = self.load_template('client.json')
            user_json = self.client_config["outbounds"][0]["settings"]["vnext"][0]
            user_json["users"][0]["id"] = self.node.password
            del user_json["users"][0]["alterId"]
            del user_json["users"][0]["security"]
            user_json["users"][0]["encryption"] = self.node.encryption
            if self.node.flow:
                user_json["users"][0]["flow"] = self.node.flow
            self.client_config["outbounds"][0]["protocol"] = "vless" 

        elif type(self.node) == Socks:
            self.client_config = self.load_template('client_socks.json')
            user_json = self.client_config["outbounds"][0]["settings"]["servers"][0]
            user_json["users"][0]["user"] = self.node.user_info
            user_json["users"][0]["pass"] = self.node.password

        elif type(self.node) == SS:
            self.client_config = self.load_template('client_ss.json')
            user_json = self.client_config["outbounds"][0]["settings"]["servers"][0]
            user_json["method"] = self.node.method
            user_json["password"] = self.node.password

        elif type(self.node) == Trojan:
            self.client_config = self.load_template('client_trojan.json')
            user_json = self.client_config["outbounds"][0]["settings"]["servers"][0]
            user_json["password"] = self.node.password

        elif type(self.node) == Mtproto:
            print("")
            print(_("MTProto protocol only use Telegram, and can't generate client json!"))
            print("")
            exit(-1)

        user_json["port"] = int(self.group.port)
        user_json["address"] = self.group.ip

        if type(self.node) != SS:
            self.client_config["outbounds"][0]["streamSettings"] = self.config["inbounds"][self.group.index]["streamSettings"]

        if self.group.tls == 'tls':
            self.client_config["outbounds"][0]["streamSettings"]["tlsSettings"] = {}
        elif self.group.tls == 'xtls':
            self.client_config["outbounds"][0]["streamSettings"]["xtlsSettings"]["serverName"] = self.group.ip
            del self.client_config["outbounds"][0]["streamSettings"]["xtlsSettings"]["certificates"]
            del self.client_config["outbounds"][0]["streamSettings"]["xtlsSettings"]["alpn"]
            del self.client_config["outbounds"][0]["mux"]
        elif self.group.tls == 'reality':
            pbkey = ''
            with open("/etc/xray/reality.key", "r") as keyf:
                for keys in keyf.readlines():
                    if self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["privateKey"] in keys:
                        pbkey = keys.split()[-1]  
            self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["pubicKey"] = pbkey
            self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["fingerprint"] = "chrome"
            self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["serverName"] = \
                self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["serverNames"][0]
            del self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["serverNames"]
            self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["shortId"] = \
                self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["shortIds"][0]
            del self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["shortIds"]
            del self.client_config["outbounds"][0]["streamSettings"]["realitySettings"]["privateKey"]
            
    def write(self):
        '''
        写客户端配置文件函数
        '''
        json_dump = json.dumps(self.client_config,indent=1)
        with open(self.write_path, 'w') as write_json_file:
            write_json_file.writelines(json_dump)

        print("{0}({1})\n".format(_("save json success!"), self.write_path))

def generate():
    cs = ClientSelector(_('generate client json'))
    if not hasattr(cs, 'client_index'):
        return
    client_index = cs.client_index
    group = cs.group

    if group == None:
        pass
    else:
        cw = ClientWriter(group, client_index)
        cw.transform()
        cw.write()
