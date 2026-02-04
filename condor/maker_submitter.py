import os
import optparse
import sys
import time
import shutil
import yaml
sys.path.append('../')

config          = {}
config_path     = os.environ.get('PWD')+'/../config/config.yaml'
if os.path.exists(config_path):
    with open(config_path, "r") as _f:
        config  = yaml.safe_load(_f) or {}
    print(f"Loaded config file from {config_path}")
else:
    print(f"Config file not found in {config_path}, exiting")
    sys.exit(1)


usage               = "python3 maker_submitter.py --year <year> --cat <cat> --dryrun"
parser              = optparse.OptionParser(usage)
parser.add_option(      "--year",           dest="year",      type=str,                             default="2023",     help="Please enter the year of the samples to check, e.g. 2022, 2022EE, etc.")
parser.add_option(      "--cat",            dest="cat",       type=str,                             default="MixLoose", help="Please enter the category to process, e.g. ResLoose, ResTight, MixLoose etc.")
parser.add_option(      '--dryrun',         dest='dryrun',                  action='store_true',    default = False,    help='dryrun')

(opt, args)         = parser.parse_args()
year                = opt.year
category            = opt.cat
dryrun              = opt.dryrun
path_to_config_file = config["make_file"][year][category]

if year not in ["2022", "2022EE", "2023", "2023postBPix", "2024"]:
    print("Please select a valid period among: 2022, 2022EE, 2023, 2023postBPix")
    sys.exit(1)



username        = str(os.environ.get('USER'))
inituser        = str(os.environ.get('USER')[0])
uid             = int(os.getuid())
workdir         = "user" if "user" in os.environ.get('PWD') else "work"
if not os.path.exists("/tmp/x509up_u" + str(uid)):
    os.system('voms-proxy-init --rfc --voms cms -valid 192:00')
os.popen("cp /tmp/x509up_u" + str(uid) + " /afs/cern.ch/user/" + inituser + "/" + username + "/private/x509up")

def sub_writer(run_folder, log_folder, year, category):
    f = open(run_folder+"condor.sub", "w")
    f.write("Proxy_filename          = x509up\n")
    f.write("Proxy_path              = /afs/cern.ch/user/" + inituser + "/" + username + "/private/$(Proxy_filename)\n")
    f.write("universe                = vanilla\n")
    f.write("x509userproxy           = $(Proxy_path)\n")
    f.write("use_x509userproxy       = true\n")
    f.write("request_cpus            = 4\n")
    # f.write("should_transfer_files   = YES\n")
    # f.write("when_to_transfer_output = ON_EXIT\n")
    f.write("transfer_input_files    = $(Proxy_path)\n")
    # f.write("transfer_output_remaps  = \""+outname+"_Skim.root=root://eosuser.cern.ch///eos/user/"+inituser + "/" + username+"/DarkMatter/topcandidate_file/"+dat_name+"_Skim.root\"\n")
    # f.write('requirements            = (TARGET.OpSysAndVer =?= "CentOS7")\n')
    f.write("+JobFlavour             = \"nextweek\"\n") # options are espresso = 20 minutes, microcentury = 1 hour, longlunch = 2 hours, workday = 8 hours, tomorrow = 1 day, testmatch = 3 days, nextweek = 1 week
    f.write('+JobTag                 = "maker_'+year+"_"+category+'"\n')
    f.write("executable              = "+run_folder+"runner.sh\n")
    f.write("arguments               = $(Proxy_path)\n")
    #f.write("input                   = input.txt\n")
    f.write("output                  = "+log_folder+"output/maker_"+year+"_"+category+".out\n")
    f.write("error                   = "+log_folder+"error/maker_"+year+"_"+category+".err\n")
    f.write("log                     = "+log_folder+"log/maker_"+year+"_"+category+".log\n")
    f.write("queue\n")
    f.close()

def runner_writer(run_folder, path_to_config_file):
    f = open(run_folder+"runner.sh", "w")
    f.write("#!/usr/bin/bash\n")
    f.write("cd /afs/cern.ch/user/" + inituser + "/" + username + "/\n")
    f.write("source topsf.sh\n")
    pycommand = f"python3 make_histograms.py {path_to_config_file}"

    f.write(pycommand+"\n")
    f.close()


if not os.path.exists("/tmp/x509up_u" + str(uid)):
    print("Please run voms command")
    exit()



######## LAUNCH CONDOR ########
condor_folder           = os.environ.get('PWD') + "/condor/"
log_folder              = condor_folder
condor_subfolder        = condor_folder + year + "_" + category + "/"
run_folder              = condor_subfolder

if not os.path.exists(condor_folder):
    os.makedirs(condor_folder)
    print(f"Creating condor folder:     {condor_folder}")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
    print(f"Creating condor folder:     {log_folder}")
if not os.path.exists(condor_subfolder):
    os.makedirs(condor_subfolder, exist_ok=True)
    print(f"Creating condor subfolder:  {condor_subfolder}")
else:
    shutil.rmtree(condor_subfolder, ignore_errors=True)
    os.makedirs(condor_subfolder, exist_ok=True)
    print(f"Creating condor subfolder:  {condor_subfolder}")

if not os.path.exists(condor_folder+"output/"):
    os.makedirs(condor_folder+"output/", exist_ok=True)
else:
    shutil.rmtree(condor_folder+"output/", ignore_errors=True)
    os.makedirs(condor_folder+"output/", exist_ok=True)
if not os.path.exists(condor_folder+"error/"):
    os.makedirs(condor_folder+"error/", exist_ok=True)
else:
    shutil.rmtree(condor_folder+"error/", ignore_errors=True)
    os.makedirs(condor_folder+"error/", exist_ok=True)
if not os.path.exists(condor_folder+"log/"):
    os.makedirs(condor_folder+"log/", exist_ok=True)
else:
    shutil.rmtree(condor_folder+"log/", ignore_errors=True)
    os.makedirs(condor_folder+"log/", exist_ok=True)



runner_writer(run_folder, path_to_config_file)
sub_writer(run_folder, log_folder, year, category)
if not dryrun:
    print("Submitting condor job for year ", year, " and category ", category)
    os.popen("condor_submit " + run_folder + "condor.sub")
time.sleep(2)