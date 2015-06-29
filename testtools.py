#!/usr/bin/python
import os
import sys
import re
import MyAPI
import MyDiskAPI


def PrintList():
    print "command\taction"
    print "1\ttest udevadm bug"
    print "2\ttest raid w/r speed"
    print "3\ttest get server info"
    print "4\ttest config status"
    print "5\ttest all"
    print "quit\tquit"
def CheckPexpect():
    res = "Installed"
    try:
        import pexpect
    except:
        res = "Not installed"
    return res
def CheckBackend():
    flag = os.access('/opt/glustermg/1.0.0alpha/backend/',os.F_OK)
    if flag:
        res = "Installed"
    else:
        res = "Not installed"
    return res
    
def CheckAlert():
    alertfile = '/opt/glustermg/1.0.0alpha/backend/alert.py'
    flag = os.access(alertfile,os.F_OK)
    confflag = False
    conf = MyAPI.readFile('/etc/crontab',lines=True)
    for line in conf:
        if re.search(alertfile,line):
            confflag = True
    
    if not flag:
        res = "Not installed"
    elif not confflag:
        res = "Not configured"
    else:
        res = "Configured"
    return res
    
def CheckSmart():
    rv = MyAPI.runCommand("which smartctl", output=True, root=True)
    if rv["Status"]!=0:
        res = "Not installed"
    else:
        rv = MyAPI.runCommand("smartctl --version", output=True, root=True)
        res = rv["Stdout"].split()[1]
    return res

    
def CheckMulticast():
    checkfile = "/etc/init.d/multicast-discoverd"
    flag = os.access(checkfile,os.F_OK)
    if flag:
        rv = MyAPI.runCommand("/etc/init.d/multicast-discoverd status", output=True, root=True)
        if re.search("running",rv["Stdout"]):
            return "ON"
        else:
            return "OFF"
    else:
        return "Not installed"    
def CheckMega():
    megafile = "/opt/MegaRAID/MegaCli/MegaCli64"
    flag = os.access(megafile,os.F_OK)
    if flag:
        return "Installed"
    else:
        return "Not installed"
    
def CheckRaidfix():
    scriptfile = "/opt/glustermg/1.0.0alpha/backend/fixraid.py"
    flag = os.access(scriptfile,os.F_OK)
    confflag = False
    conf = MyAPI.readFile('/etc/udev/rules.d/60-raw.rules',lines=True)
    for line in conf:
        if re.search(scriptfile,line):
            confflag = True
    
    if not flag:
        return "Not installed"
    elif not confflag:
        return "Not configured"
    else:
        return "Configured"
        
def CheckGlobals():
    try:
        sys.path.append("/opt/glustermg/1.0.0alpha/backend/")
        import Globals
        hardconf = Globals.HARDWARE_CONFIG
    except:
        hardconf = "MISS"
    return hardconf
    
def CheckAll():
    print "Test configure satus\n"
    print "checking backend install\t\t",
    sys.stdout.flush()
    print CheckBackend()
    print "checking alert install\t\t\t",
    sys.stdout.flush()
    print CheckAlert()
    print "checking S.M.A.R.T install\t\t",
    sys.stdout.flush()
    print CheckSmart()
    print "checking Raidfix install\t\t",
    sys.stdout.flush()
    print CheckRaidfix()
    print "checking multicast install\t\t",
    sys.stdout.flush()
    print CheckMulticast()
    print "checking MegaCli install\t\t",
    sys.stdout.flush()
    print CheckMega()
    print "checking Pexpect install\t\t",
    sys.stdout.flush()
    print CheckPexpect()
    print "checking Globals Conf install\t\t",
    sys.stdout.flush()
    print CheckGlobals()
    print ""

def TestAll():
   TestUdevBug()
   TestRaidSpeed()
   TestGetinfo()
   CheckAll()
def TestGetinfo():
    print "Testing get info config\n"
    print "Testing get_server_info\t\t",
    sys.stdout.flush()   
    rv = MyAPI.runCommand("/opt/glustermg/1.0.0alpha/backend/get_server_details.py", output=True, root=True)
    if rv["Status"]==0:
        print "pass"
    else:
        print "failed"
    print "Testing get_server_brick\t",
    sys.stdout.flush()   
    rv = MyAPI.runCommand("/opt/glustermg/1.0.0alpha/backend/get_server_bricks.py", output=True, root=True)
    if rv["Status"]==0:
        print "pass"
    else:
        print "failed"
    print ""
    
def TestUdevBug():
    res = 0
    disklist = MyDiskAPI.getDiskList()
    print "Testing udevadm bug\n\nTest Complate :    ",
    for i in range(1000):
        print "\b\b\b\b%2d%%"%(i/10),
        #time.sleep(0.01)
        sys.stdout.flush()
        for device in disklist:
            rv = MyAPI.runCommand("udevadm info -a -p /sys/block/%s " % device , output=True, root=True)
            if not rv["Status"]==0:
                res=res+1
    print "\b\b\b\bDone"
    print "pass the test with result:%d\n"%res
    print ""
    return 0

def runReadWrite(testdir):
    print ("w/r performance test\n\noption\tsize\tspeed")
    for i in range(1,15,3):
        rv = MyAPI.runCommand("dd if=/dev/zero of=%s/testfile%d bs=%dM count=1024"% (testdir,i,i), output=True, root=True)
        for line in rv["Stderr"].split('\n'):
            if line.count('bytes')!=0:
                speed = line.split(',')[-1]
                size = line.split('(')[1].split(')')[0]
                print ("write\t%s\t%s"%(size,speed))
        rv = MyAPI.runCommand("dd of=%s/testfile%d if=/dev/zero bs=%dM count=1024"% (testdir,i,i), output=True, root=True)
        for line in rv["Stderr"].split('\n'):
            if line.count('bytes')!=0:
                speed = line.split(',')[-1]
                size = line.split('(')[1].split(')')[0]
                print ("read\t%s\t%s"%(size,speed))
def TestRaidSpeed(testdir=None):
    print "Testing RaidSpeed\n"
    if not testdir:
        testdir = "/testdir"
    diskspace = MyDiskAPI.isDirMounted(testdir)
    if diskspace == 0:
        print "\"/testspeed\" not mounted, you should mount your disk/raid to /testspeed dir manually."
    elif diskspace <0:
        print "ERROR:someting wrong Encountered. check your Operation system."
    elif diskspace < 51606140:
        print "your test device is not large enough. it should be more then 50G for test."
    else:
        runReadWrite(testdir)
    print ""
        
def main():
    print "Gluster data-node Test Tools\n"
    while 1:
        PrintList()
        getinput = raw_input("Select Option : ")
        if getinput =="quit":
            break
        elif getinput == "1":
            TestUdevBug()
        elif getinput == "2":
            TestRaidSpeed()
        elif getinput == "3":
            TestGetinfo()
        elif getinput == "4":
            CheckAll()
        elif getinput == "5":
            TestAll()
    
if __name__ == "__main__":
    main()
    
