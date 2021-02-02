""" ProcMan """

import yaml
import os.path

class Config:
    def __init__(self, config_path):
        self.path = config_path
        self.services = {}

    def parse_yaml(self):
        with open(self.path) as cf:
            docs = yaml.load_all(cf, Loader=yaml.Loader)
            for doc in docs:
                self.services[doc["name"]]=doc["procman"]
                # fixme add try on keys

    def service_list(self):
        return list(self.services.keys())

    def java_config(self, service_name):
        jc = JavaConfig(self.services[service_name]["java"])
        return jc.validated()

class JavaConfig(Config):

    def __init__(self, java_params):
        self.params = java_params
        self.validators = { 'vmpath': self._check_path,
                'debug': self._check_debug}

    def validated(self):
        self._check_required()
        for p in self.params:
            print ("Param: " + p    )
            if p in self.validators:
                self.validators[p](self.params[p])

    def _check_required(self):
        for r in ('classpath','main'):
            if not r in self.params:
                raise InvalidConfigException("no required param: [%s]" % r)

    def _check_path(self, value):
        if not os.path.isfile(value):
            raise InvalidConfigException("Java bin path is not file: [%s]" % value)

    def _check_debug(self, value):
        if not (value == True or value == False):
            raise InvalidConfigException("Invalid debug value: [%s]" % value)
    
class InvalidConfigException(Exception):
    pass

if __name__ == "__main__":
    conf = Config("services.yaml")
    conf.parse_yaml()
    print("services: ", conf.service_list())
    conf.java_config('echo')

