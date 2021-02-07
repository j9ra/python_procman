""" ProcMan """

import yaml
import os.path
import re
import glob
import datetime
import subprocess
import logging
import logging.config
import zipfile

logger = logging.getLogger('procman')

class Config:
    def __init__(self):
        self.services = {}

    def parse_yaml(self, config_path):
        with open(config_path) as cf:
            docs = yaml.load_all(cf, Loader=yaml.Loader)
            try:
                for doc in docs:
                    self.services[doc["name"]]=doc["procman"]
            except KeyError as exc:
                print("Not procman Config loaded!") 
                raise InvalidConfigException("Format error") from exc

    def service_list(self):
        return list(self.services.keys())

    def java_config(self, service_name):
        if not "java" in self.services[service_name]:
            return None
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
        logger.debug("Param get %s, value %s", item, self.params.get(item))
        return self.params.get(item)

    def validated(self):
        self._check_required()
        for p in self.params:
            logger.debug("Validating config param [%s]" % p)
            if p in self.validators:
                self.validators[p](self.params[p])
            else:
                logger.warn("unrecognized config param [%s]", p)
        self._check_pom_duplicates(self.classpath)

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
    
    def _check_pom_duplicates(self, classpath):
        pom_artifacts = {}
        for cp in classpath:
            pom_file = self._jar_extract_pom(cp)
            if pom_file:
                pom_props = self._properties_parse(pom_file)
                key = (pom_props["groupId"], pom_props["artifactId"])
                val = {"file": cp, "version": pom_props["version"]}
                if key in pom_artifacts:
                    pom_artifacts[key].append(val)
                else:
                    pom_artifacts[key] = [val]
        # check duplicates
        for group,arti in pom_artifacts.keys():
            files = pom_artifacts[(group,arti)]
            if len(files) > 1: # found dups
                logger.warn("Found classpath artifact duplicates for group: %s, artifact: %s, files: %s", group, arti, files)


    def _jar_extract_pom(self, jar_filename, properties_file = "pom.properties", encoding = "utf-8"):
        properties = None
        archive = zipfile.ZipFile(jar_filename, 'r')
        for i in archive.infolist():
            if i.filename.endswith(properties_file):
                content = archive.read(i.filename)
                properties = content.decode(encoding)
        return properties
    
    def _properties_parse(self, multiline_text,sep='=', comment_char='#'):
        props = {}
        for line in multiline_text.splitlines():
            l = line.strip()
            if l and not l.startswith(comment_char):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"') 
                props[key] = value 
        return props
    
class InvalidConfigException(Exception):
    pass

class JLauncher:

    def __init__(self, java_config):
        self.config = java_config
        self.proc_handle = None
        self.stream_out = None

    def build_command(self):
        cmd_line = []
        # binary path
        cmd_line.append(self.config.vmpath)
        # debug
        if self.config.debug == True:
            cmd_line.append("-agentlib:jdwp=transport=dt_socket,server=y,suspend=y")
        # memory
        if self.config.memory:
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
        if self.config.sysprops:
            for p in self.config.sysprops:
                cmd_line.append("-D%s" % p)
        # classpath, must be 2 seperate args!
        cmd_line.append("-classpath")
        cmd_line.append(os.pathsep.join(self.config.classpath))
        # main
        cmd_line.append(self.config.main)
        # args
        if self.config.args:
            for a in self.config.args:
                cmd_line.append(a)

        logger.debug("cmdline as tab %s", cmd_line)
        logger.debug("Cmdline: %s" % " ".join(cmd_line))
        return cmd_line

    def redirect_streamout(self):
        if not self.config.streamout:
            return None
        # make output filename more uniq
        if self.config.streamout.endswith("$$"):
            basename = self.config.streamout[:-2]
            suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "_".join([basename, suffix])
        else:
            filename = self.config.streamout
        self.stream_out = open(filename, mode="a")
        logger.info("Redirecting output to file: %s", filename)
        return self.stream_out
        
    def run(self):
        if self.is_running():
            logger.warn("Proc already running!")
            return None

        cmd = self.build_command()
        out_file = self.redirect_streamout()
        try:
            if out_file: 
                # redirect output stream
                self.proc_handle = subprocess.Popen(cmd,
                    stdout=out_file, stderr=subprocess.STDOUT)
            else:
                self.proc_handle = subprocess.Popen(cmd)
        except OSError as e:
            print("Failed to run proc", str(e))
            return None

        logger.info("Proc %s PID %d" %
            (self.proc_handle.args[0], self.proc_handle.pid))
        return self.proc_handle.pid

    def stop(self):
        if self.is_running():
            # send TERM and wait
            self.proc_handle.terminate()
            self.proc_handle.wait()
            # clear stream output handle
            if self.redirect_streamout:
                self.stream_out.close()
            return self.proc_handle.returncode

    def is_running(self):
        if not self.proc_handle:
            return False
        # check if dead, otherwise it still lives
        status = self.proc_handle.poll()
        return True if status==None else False

class ProcessManager:

    def __init__(self, work_dir, config_file="services.yaml", init_logging=False, logging_conf="logging.conf"):
        os.chdir(work_dir)
        self.curr_dir = os.getcwd()
        self.service_config_file = config_file
        self.services_registry = {}
        if init_logging:
            self._init_logging(logging_conf)
        logger.info("Initialing from [%s] in workdir: [%s]" % (self.service_config_file, self.curr_dir))
        self._configure()
        logger.info("Now ready for bussiness!")
        

    def _configure(self):
        self.conf = Config()
        self.conf.parse_yaml(self.service_config_file)
        logger.info("Found services config in file [%s]" % self.service_config_file )
        for serv in self.conf.service_list():
            # maybe in future support others then Java, if so plug it here!
            try:
                java_config = self.conf.java_config(serv)
                java_launcher = JLauncher(java_config)
                # registry by service name
                self.services_registry[serv] = java_launcher
                logger.info("Service [%s] bound to registry", serv)
            except InvalidConfigException as e:
                logger.error("Service [%s] init failed!, error: %s", serv, str(e))

    def _init_logging(self,logging_conf):
        logging.config.fileConfig(logging_conf)
        logger.info("Logging enabled, config=%s" % logging_conf)

    def list(self):
        return list(self.services_registry.keys())

    def start(self, service_name):
        if not service_name in self.services_registry:
            return None
        logger.info("Starting service [%s]" % service_name)
        return self.services_registry[service_name].run()

    def stop(self, service_name):
        if not service_name in self.services_registry:
            return None
        logger.info("Stopping service [%s]" % service_name)
        return self.services_registry[service_name].stop()

    def status(self, service_name):
        if not service_name in self.services_registry:
            return None
        logger.info("Checking status of service [%s]" % service_name)
        return self.services_registry[service_name].is_running()
      


if __name__ == "__main__":
    
    proc_man = ProcessManager(os.getcwd(),init_logging=True)
    print("Service list:", proc_man.list())

    pid = proc_man.start('echo')
    print("echo PID %s" % pid)
    import time
    time.sleep(10)
    print("Is running? ", proc_man.status('echo'))
    time.sleep(10)
    print("Stopping")
    print("returncode",proc_man.stop('echo'))
    print("Stopped")
    print("Is running? ", proc_man.status('echo'))