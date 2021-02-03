""" ProcMan """

import yaml
import os.path
import re
import glob

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
        jc.validated() # raise on invalid conf
        return jc

class JavaConfig(Config):

    def __init__(self, java_params):
        self.params = java_params
        self.validators = { 
            'vmpath': self._check_path,
            'debug': self._check_debug,
            'memory': self._check_memory,
            'gc': self._check_gc,
            'classpath': self._check_classpath,
            'sysprops': self._check_sysprops,
            'main': self._check_main,
            'args': self._check_args,
            'streamout': self._check_streamout}

    @property
    def vmpath(self):
        return self.params.get("vmpath","java")
            
    @property
    def classpath(self):
        cp_tab = []
        # globbing 
        for c in self.params.get("classpath"):
            if re.search(r"[\?\*\[\]]", c):
                for gg in glob.glob(c):
                    cp_tab.append(gg)  
            else: 
                cp_tab.append(c)
        return cp_tab

    def __getattr__(self, item):
        return self.params.get(item)

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

    def _check_memory(self, value):
        types = ("min","max","meta")
        for t,v in value.items():
            if not (t in types and re.fullmatch(r"\d+(k|m|g)",str(v))):
                raise InvalidConfigException("Invalid mem value: [%s=%s]" % (t,v))

    def _check_gc(self, value):
        if not value in ("serial","parallel","cms","g1"):
            raise InvalidConfigException("Invalid gc value: [%s]" % value)

    def _check_classpath(self, value):
        for c in value:
            if not (c and re.fullmatch(r"[\S]+", c)):
                raise InvalidConfigException("Invalid classpath: [%s]" % c)

    def _check_sysprops(self, value):
        for p in value:
            if len(p.split("=")) != 2:
                raise InvalidConfigException("Invalid sysprop: [%s]" % p)

    def _check_main(self, value):
        if not re.fullmatch(r"(?:\w+\.)*\w+", value):
            raise InvalidConfigException("Invalid main: [%s]" % value)

    def _check_args(self, value):
        if not (value and type(value) is list):
            raise InvalidConfigException("Invalid args: [%s]" % value)

    def _check_streamout(self, value):
        if os.path.isfile(value) and not os.access(value,os.W_OK):
            raise InvalidConfigException("Streamout not writeable: [%s]" % value)
    
class InvalidConfigException(Exception):
    pass

class JLauncher:

    def __init__(self, java_config):
        self.config = java_config

    def build_command(self):
        cmd_line = []
        # binary path
        cmd_line.append(self.config.vmpath)
        # debug
        if self.config.debug == True:
            cmd_line.append("-agentlib:jdwp=transport=dt_socket,server=y,suspend=y")
        # memory
        if "min" in self.config.memory:
            cmd_line.append("-Xms%s" % self.config.memory.get("min"))
        if "max" in self.config.memory:
            cmd_line.append("-Xmx%s" % self.config.memory.get("max"))
        if "meta" in self.config.memory:
            cmd_line.append("-XX:MaxMetaspaceSize=%s" % self.config.memory.get("meta"))
        # gc
        if self.config.gc == "serial":
            cmd_line.append("-XX:+UseSerialGC")
        elif self.config.gc == "parallel":
            cmd_line.append("-XX:+UseParallelGC")
        elif self.config.gc == "cms":
            cmd_line.append("-XX:+UseConcMarkSweepGC")
        elif self.config.gc == "g1":
            cmd_line.append("-XX:+UseG1GC")
        # sysprops
        for p in self.config.sysprops:
            cmd_line.append("-D%s" % p)
        # classpath
        cmd_line.append("-classpath %s" % os.pathsep.join(self.config.classpath))
        # main
        cmd_line.append(self.config.main)
        # args
        for a in self.config.args:
            cmd_line.append(a)


        print("Cmdline: %s" % " ".join(cmd_line))


if __name__ == "__main__":
    conf = Config("services.yaml")
    conf.parse_yaml()
    print("services: ", conf.service_list())
    jc = conf.java_config('echo')
    print (dir(jc))
    print ("debug:",jc.debug)
    print ("main:",jc.main)
    print ("bogus:",jc.bogus)
    print ("vmpath:",jc.vmpath)
    
    jl = JLauncher(jc)
    jl.build_command()

