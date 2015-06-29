#!/usr/bin/python
import os
import sys
p1 = os.path.abspath(os.path.dirname(sys.argv[0]))
p2 = "%s/common" % os.path.dirname(p1)
if not p1 in sys.path:
    sys.path.append(p1)
if not p2 in sys.path:
    sys.path.append(p2)
import glob
import pickle
import types
import MyAPI





def getDeviceName(device):
    if type(device) == type([]):
        nameList = []
        for d in device:
            nameList.append(_stripDev(d))
        return nameList
    return _stripDev(device)


def getDevice(deviceName):
    if MyAPI.isString(deviceName):
        return _addDev(deviceName)
    if type(deviceName) == type([]):
        nameList = []
        for d in deviceName:
            nameList.append(_addDev(d))
        return nameList
    return _addDev(deviceName)


def getDiskPartitionByUuid(uuid):
    uuidFile = "/dev/disk/by-uuid/%s" % uuid
    if os.path.exists(uuidFile):
        return getDeviceName(os.path.realpath(uuidFile))
    return None


def getUuidByDiskPartition(device):
    for uuidFile in glob.glob("/dev/disk/by-uuid/*"):
        if os.path.realpath(uuidFile) == device:
            return os.path.basename(uuidFile)
    return None


def getDiskPartitionByLabel(label):
    ## TODO: Finding needs to be enhanced
    labelFile = "/dev/disk/by-label/%s" % label
    if os.path.exists(labelFile):
        if os.path.islink(labelFile):
            return getDeviceName(os.path.realpath(labelFile))
    return None

def getDeviceMountPoint(device):
    lines = MyAPI.readFile("/proc/mounts", lines=True)
    uuid = getUuidByDiskPartition(device)
    for line in lines:
        tokens = line.split()
        if tokens[0] == device or (uuid and tokens[0].endswith(uuid)):
            return tokens[1]
    return None
def isDirMounted(mountpoint):
    mountflag = 0
    errorflag = 0
    lines = MyAPI.readFile("/proc/mounts", lines=True)
    for line in lines:
        tokens = line.split()
        if tokens[1] == mountpoint:
            mountflag = 1
    if mountflag == 1:
        rv = MyAPI.runCommand(["df", mountpoint], output=True)
        if rv["Status"] == 0:
            try:
                diskspace = long(rv["Stdout"].split("\n")[1].split()[2])
            except IndexError, e:
                errorflag=1
            except ValueError, e:
                errorflag=1
        if not errorflag == 1:
            return diskspace
        else:
            return -1
    else:
        return 0
        
def getProcPartitions():
    procPartitionsDict = {}
    s = MyAPI.readFile("/proc/partitions", lines=True)
    for line in s[2:]:
        tokens = line.strip().split()
        procPartitionsDict[tokens[3]] = {"Size" : long(tokens[2])}
    return procPartitionsDict

def getProcMdstat():
    raidArrayDict = {}
    lines = MyAPI.readFile("/proc/mdstat", lines=True)
    for line in lines[1:]:
        tokens = line.strip().split()
        if not tokens:
            continue
        if tokens[0].startswith("md"):
            raidArrayDict[tokens[0]] = {"Status" : tokens[2], "Type" : tokens[3], "Member" : [token.split('[')[0] for token in tokens[4:]]}
    return raidArrayDict

def isBrick(device):
    lines = MyAPI.readFile("/proc/mounts", lines=True)
    uuid = getUuidByDiskPartition(device)
    device = getDevice(device)
    for line in lines:
        tokens = line.split()
        if tokens[0] == device or (uuid and tokens[0].endswith(uuid)):
            if tokens[1] in glob.glob("/brick/*"):
            	  return True            
    return False

def getDiskSiteList():
    sitelist = {}
    try:
        tmpfile = open('/opt/glustermg/1.0.0alpha/backend/disksite.map','rb')
        sitelist = pickle.load(tmpfile)
        tmpfile.close()
    except:
        sitelist = {}
    return sitelist

def getDiskSite_9220_3U16(device):
    res = {}
    diskmap ={}
    res["name"]=device
    res["target"]=None
    rv = MyAPI.runCommand("udevadm info -a -p /sys/block/%s " % device , output=True, root=True)

    resorce=rv["Stdout"].strip().split('\n')
    for i in resorce:
        if i.strip().startswith('KERNELS'):
            if i.split('==')[1].strip('"').startswith('target'):
                res["target"]=i.split('==')[1].strip('"').split(":")[-1]
    tmpsite = res["target"]
    diskmap = getDiskSiteList()
    try:
        disksite = diskmap[tmpsite]
    except:
        disksite = None
    return disksite
    
def getDiskSite_9220_3U16_M(device):
    if device in MegaDiskMap:
        return MegaDiskMap[device]
    else:
        return None
        
def getDiskSite_9220_2U12(device):
    res = {}
    diskmap ={}
    res["name"]=device
    res["target"]=None
    res["host"]=None
    res["ID"]=None
    rv = MyAPI.runCommand("udevadm info -a -p /sys/block/%s " % device , output=True, root=True)

    resorce=rv["Stdout"].strip().split('\n')
    for i in resorce:
        if i.strip().startswith('KERNELS'):
            if i.split('==')[1].strip('"').startswith('target'):
                res["target"]=i.split('==')[1].strip('"').split(":")[-1]
            elif i.split('==')[1].strip('"').startswith('host'):
                res["host"]=i.split('==')[1].strip('"')
    if res["target"]!='0':
        tmpsite = res["target"]
    else:
        tmpsite = res["host"]
    diskmap = getDiskSiteList()    
    try:
        disksite = diskmap[tmpsite]
    except:
        disksite = None
    return disksite

def saveDiskSite(device,disksite):
    try:
        rdfile = open('disksitefile','rb')
        site=pickle.load(rdfile)
        if type(site)!= types.DictType:
            raise TypeError
        rdfile.close()
    except:
        site={}
    site[device]= disksite
    wtfile = open('disksitefile','wb')
    pickle.dump(site,wtfile)
    wtfile.close()

def getDiskSite_default(device):
    res = {}
    res["name"]=device
    res["host"]=None
    res["phy"]=None
    res["port"]=None
    rv = MyAPI.runCommand("udevadm info -a -p /sys/block/%s " % device , output=True, root=True)

    resorce=rv["Stdout"].strip().split('\n')
    for i in resorce:
        if i.strip().startswith('KERNELS'):
            if i.split('==')[1].strip('"').startswith('host'):
                res["host"]=i.split('==')[1].strip('"')
            elif i.split('==')[1].strip('"').startswith('port'):
                res["port"]=i.split('==')[1].strip('"')
            elif i.split('==')[1].strip('"').startswith('target'):
                res["target"]=i.split('==')[1].strip('"')
    rv = MyAPI.runCommand("ls /sys/bus/scsi/devices/%s/%s/"% (res["host"],res["port"]),output=True, root=True)

    resorce=rv["Stdout"].strip().split()
    for i in resorce:
        if i.startswith("phy"):
            res["phy"]=i
    if res["host"]!=None and res["phy"]!=None:
        disksite = int(res["host"][-1])*8+int(res["phy"][-1])+1
    else:
        disksite = None
    return disksite

def getDiskSite(device):
        return None

def getDiskSitebyfile(device):
    site = None
    try:
        testfile = open('disksitefile','rb')
        sitelist = pickle.load(testfile)
        site = sitelist[device]
        testfile.close()
    except:
        site = None
    return site


def getDiskList():
    disklist=list()
    partitionsInfo = getProcPartitions()
    for name,value in partitionsInfo.iteritems():
        if name.startswith('sd') and not name[-1].isdigit():
            disklist.append(name)
    return disklist

def isRaidClean():
    status = True
    mdlist = getProcMdstat()
    for raidname in  mdlist:
        #print raidname
        status=False
        mdinfo = MyAPI.runCommand("mdadm -D /dev/%s" % raidname,output=True,root=True)
        if mdinfo["Status"]==0:
            for line in mdinfo["Stdout"].strip().split("\n"):
                if line.strip().startswith("State"):
                    state = line.split(":")[1].strip()
                    if state == "active" or status == "clean":
                        status = True
    return status

