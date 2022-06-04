from asyncore import write
from hashlib import md5
from operator import mod
import os
from posixpath import split
import shutil
import string
import subprocess
import requests
import json
from flask import Flask, Response
import time

API_KEY = ""

global assetsTypes;

assetsTypes = ["MAIN", "MOVIE_H", "MOVIE_L", "VOICE", "CHAR_LIST", "FULLVOICE", "PROLOGUE_VOICE", "PROLOGUE_MAIN", "CONFIG"]

#######################################################
# For testing only, will get deleted and reimplemented
#######################################################
global key_count
global hash_map



# This function return the endpoint where the assets json are store in magia server!
def endpoint_assets_list(assetType: str) -> str:

	if not assetType in assetsTypes:
		return "Invalid asset type"
	
	GAME_ENDPOINT = "http://android.magi-reco.com"
	MASTER_PATH = "/magica/resource/download/asset/master/"
	
	# Assets Types
	# Coverted to dictionary implementation to avoid branches
	assetTypesDict = {};
	assetTypesDict['MAIN']              = "asset_main.json"
	assetTypesDict['MOVIE_H']           = "asset_movie_high.json"
	assetTypesDict['MOVIE_L']           = "asset_movie_low.json"
	assetTypesDict['VOICE']             = "asset_voice.json"
	assetTypesDict['CHAR_LIST']         = "asset_char_list.json"
	assetTypesDict['FULLVOICE']         = "asset_fullvoice.json"
	assetTypesDict['PROLOGUE_VOICE']    = "asset_prologue_voice.json"
	assetTypesDict['PROLOGUE_MAIN']     = "asset_prologue_main.json"
	assetTypesDict['CONFIG']            = "asset_config.json"
	assetTypesDict['MASTER']            = ""
	
	# Constructors of Endpoint URL
	return GAME_ENDPOINT + MASTER_PATH + assetTypesDict[assetType]


# Get Asset List from the endpoint
# Download json and json.gz files from original game server
def get_assets_list(assetType: str) -> None:
	# Get the endpoint of the assets list
	endpoint = endpoint_assets_list(assetType)
	
	# Asset Name
	assetName = endpoint.split('/')[-1]
	
	# Get the json from the endpoint
	response = requests.get(endpoint)
	
	with open(assetName, 'w') as outfile:
		json.dump(response.json(), outfile)
		
	with open(assetName + '.gz', 'w') as outfile:
		json.dump(response.json(), outfile)

	print('[ASSETS] ' + assetName + ' downloaded!')

	return None

####################################################
# Can be modified to take a list of modified files
####################################################
# Get all files in the modify folder and return md5 hash, file name and file size
# Calculates MD5 hash for files
def get_modify_files() -> list:
	print ("[MODIFY] Walking directories")
	start_time = time.time()
	files = []
	filesPath = []
	
	# Detects all file recursively in the modify folder and move files to father folder
	for root, dirnames, filenames in os.walk('magica'):
		# ignore .git file and remove it 
		if root.find('.git') != -1:
			continue
	
		for filename in filenames:
			filesPath.append(os.path.join(root, filename))    
	
	for file in filesPath:    
		file_path = os.path.join(file)    

		if os.path.isfile(file_path):
			files.append({
				"fileName": os.path.basename(file_path),
				"fileSize": os.path.getsize(file_path),
				"fileMD5": md5(open(file_path, 'rb').read()).hexdigest()
			})
			
	print ("[MODIFY] Done walking! (%s seconds)" % (time.time() - start_time))

	return files


# Move modified asset_*.json files to magica/resource/download/asset/master
# moves modified files to proper location
def move_modified_assets_json() -> None:
	for assetType in assetsTypes:
		
		if assetType == "CONFIG":
			continue
		
		assetName = endpoint_assets_list(assetType).split('/')[-1];
		root = os.path.dirname(os.path.abspath(__file__))
		shutil.move(os.path.join(root, assetName),  os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName))
	
	print('[ASSETS] All modified assets moved to magica/resource/download/asset/master!')

	return None

# Modify All Assets Types
# Calls other functions that execute modify
def modify_all() -> None:
	
	assetsModified = get_modify_files()
			
	modify_assets_json_hash(assetsModified)


# Download Repository
# Checks if the repo has be downloaded and pulls or clones
def download_repo() -> string:

	# if have a local repository, pull it
	if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'magica')):
		print('[REPO] Pulling local repository...')
		os.system('cd magica && git pull')
		print('[REPO] Pulled local repository!')
		return (subprocess.check_output("cd magica && git rev-parse HEAD", shell=True))
	else:
		print('[REPO] Downloading repository...')
		os.system('git clone ' + "https://github.com/ magica")
		print('[REPO] Downloaded!')
		return ""
		
	




##############################################
# Additions start here
##############################################
# Takes a list of calculated MD5, names, and sizes and replaces the values in the original files
# Modified version of modify_assets_json()
def modify_assets_json_hash(assetsModified):
	root = os.path.dirname(os.path.abspath(__file__))
	for assetModified in assetsModified:
		assetModifiedName = assetModified['fileName']
		assetInfo = get_asset_hash(assetModifiedName)
		if assetInfo == None:
			#print(assetModifiedName)
			continue
		assetIndex = assetInfo[0]["index"]
		assetType = assetInfo[0]["assetType"]
		assetName = endpoint_assets_list(assetType).split('/')[-1];
		with open(os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName)) as data:
			assets = json.load(data)

			asset = assets[assetIndex]

			#print(assetInfo)
			if (assetInfo[0]["file_list"]):
				fileAsset = asset["file_list"][assetInfo[0]["file_list_index"]]
				originalSize = fileAsset['size']
				modifiedSize = assetModified['fileSize']

				print("Modified File: " + assetName)
				print(f'[{assetModifiedName}] Size: {modifiedSize} -> {originalSize}')

				fileAsset['size'] = assetModified['fileSize']

			# Modify File List in the asset
			else:
				originalMD5 = asset['md5']
				modifiedMD5 = assetModified['fileMD5']

				print("Modified File: " + assetName)
				print(f'[{assetModifiedName}] MD5: {modifiedMD5} -> {originalMD5}')
				
				asset['md5'] = assetModified['fileMD5']


# Gets index and asset type for any input asset name
def get_asset_hash(assetName):
	#with open("hash_keys.json", "r") as readFile:
	#	key_count = int(readFile.read())
	#with open("hash_map.json", "r") as hash_file:
	#	hash_map = json.load(hash_file)
	for item in hash_map[int(md5(assetName.encode('utf-8')).hexdigest(), 16)%key_count]:
		if(assetName == item["assetName"]):
			return([{"index": item["index"], "assetType": item["assetType"], "file_list": item["file_list"], "file_list_index": item["file_list_index"]}])
	return None


# Pulls repo and check for changes made between the current and previous commit
def modify_changed(prev_commit, curr_commit):
	changes = []

	command = "cd magica && git diff --name-only" + " " + str(prev_commit) + " " + str(curr_commit)
	changed_output = str(subprocess.check_output(command, shell=True))
	changed_output = changed_output.replace("b'", "")

	changes = changed_output.split("\\n")
	# pop last element due to \n contamination
	changes.pop()

	for change in changes:
		change = change.replace("/", "\\\\")

	get_modify_changed_files(changes)



###########################################################
# Need to change to maybe use paths instead of file names
###########################################################
# Create hashmap and dump to file
def generate_hash_map():
	start_time = time.time()
	count = 0
	root = os.path.dirname(os.path.abspath(__file__))
	for assetType in assetsTypes:
		if assetType != "CONFIG": 
			assetName = endpoint_assets_list(assetType).split('/')[-1];
			with open(os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName)) as file:
				assets = json.load(file)
				for asset in assets:
					count+=1
					#print("[", assetName, "]", asset["path"].split("/")[-1])

	print("[HASH MAP] Found ", count, "keys")
	# create dictionary of size count
	hash_map = [[] for _ in range(count)]

	for assetType in assetsTypes:
		if assetType != "CONFIG": 
			assetName = endpoint_assets_list(assetType).split('/')[-1];
			with open(os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName)) as file:
				assets = json.load(file)
				index = 0
				for asset in assets:
					#print(int(md5(asset["path"].split("/")[-1].encode('utf-8')).hexdigest(), 16)%count)
					index += 1
					hash_map[int(md5(asset["path"].split("/")[-1].encode('utf-8')).hexdigest(), 16)%count].append({"assetName": asset["path"].split("/")[-1], "assetType": assetType, "index":index, "file_list":False, "file_list_index": 0})
					if len(asset["file_list"]) > 1:
						innerIndex = 0
						for file_listed in asset["file_list"]:
							hash_map[int(md5(file_listed["url"].split("/")[-1].encode('utf-8')).hexdigest(), 16)%count].append({"assetName": file_listed["url"].split("/")[-1], "assetType": assetType, "index":index, "file_list":True, "file_list_index": innerIndex})
							innerIndex += 1
						
						#print ("MULTIPLE!", asset["path"].split("/")[-1], assetType)

	with open("hash_map.json", "w") as write_file:
		json.dump(hash_map, write_file, indent=4)

	with open("hash_keys.json", "w") as write_file:
		write_file.write(str(count))
	print("[HASH MAP] Done! (%s seconds)" % (time.time() - start_time))







####################################
# Still need some more work
####################################
# Clones repo
# Setup the environment to start working, download repo and calculate the initial MD5 hashes for json/json.gz
def first_time_setup():
	download_repo()
	for assetType in assetsTypes:
		if(assetType != "CONFIG"):
			get_assets_list(assetType)
			with open(endpoint_assets_list(assetType).split('/')[-1] + ".md5", 'w') as outfile:
				outfile.write(md5(open(endpoint_assets_list(assetType).split('/')[-1], 'rb').read()).hexdigest())
			assetName = endpoint_assets_list(assetType).split('/')[-1];
			root = os.path.dirname(os.path.abspath(__file__))
			shutil.move(os.path.join(root, assetName),  os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName))
			shutil.move(os.path.join(root, assetName + ".md5"),  os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName + ".md5"))
	
	generate_hash_map()

	with open("hash_keys.json", "r") as readFile:
		global key_count
		key_count = int(readFile.read())
	with open("hash_map.json", "r") as hash_file:
		global hash_map
		hash_map = json.load(hash_file)

	modify_all()




# Calculated MD5 hashed for modified files since last commit
def get_modify_changed_files(changes:list) -> list:
	files = []

	root = os.path.dirname(os.path.abspath(__file__)) + "/magica/"
	for change in changes:
		files.append({
			"fileName": os.path.basename(root + change),
			"fileSize": os.path.getsize(root + change),
			"fileMD5": md5(open(root + change, 'rb').read()).hexdigest()
		})

	print(files)


# Cleans the output that comes from extracting commit hash
def clean_git_output(output:string):
	output = output.replace("b'", "")
	output = output.replace("\\n'", "")
	output = output.replace("b'", "")
	output = output.replace("\\n'", "")

	return output


def check_download_asset_diff():
	newMD5 = ""
	oldMD5 = ""
	difference = False
	root = os.path.dirname(os.path.abspath(__file__))
	for assetType in assetsTypes:
		assetName = endpoint_assets_list(assetType).split('/')[-1];
		if assetType != "CONFIG":
			get_assets_list(assetType)
			newMD5 = md5(open(endpoint_assets_list(assetType).split('/')[-1], 'rb').read()).hexdigest()
			oldMD5 = open(os.path.join(root, 'magica', 'resource', 'download', 'asset', 'master', assetName + ".md5")).read()
			if newMD5 == oldMD5:
				print(f'[ASSET LIST DIFF] {assetName} has no changes!')
			else:
				difference = True
				print(f'[ASSET LIST DIFF] {assetName} has changes!')
				return difference
	return difference





##############################################
##############################################
# Function executions and flask server
##############################################
# Uncomment for first time run
#first_time_setup()

#download_repo()
#modify_all()

#generate_hash_map()

#check_download_asset_diff()

# Servidor que va hacer que actualice el repo 
server = Flask(__name__)

@server.route('/api/pull/<apiKey>', methods=['POST'])
def postPull(apiKey):

	if apiKey != API_KEY:
		return "Invalid API Key"

	response = Response('Process Started Successfully!')
	
	@response.call_on_close
	def on_close():
		if os.path.isfile("hash_map.json"):		# Check if hash_map.json file exists
			with open("hash_keys.json", "r") as readFile:
				global key_count
				key_count = int(readFile.read())
			with open("hash_map.json", "r") as hash_file:
				global hash_map
				hash_map = json.load(hash_file)
			if(check_download_asset_diff()):	# Compare json.gz files with ones from server
				first_time_setup()
			else:
				prev_commit = ""
				curr_commit = ""

				if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'magica')):
					prev_commit = str(subprocess.check_output("cd magica && git rev-parse HEAD", shell=True))
					prev_commit = clean_git_output(prev_commit)


				# Cleanup command line output
				curr_commit = str(download_repo())
				curr_commit = clean_git_output(curr_commit)

				if prev_commit != curr_commit:
					print("[REPO] Difference")
					modify_changed(prev_commit, curr_commit)
				else:
					print ("[REPO] No changes!")
					
		else:
			first_time_setup()

		# Test to see if hash map lookup is working as intended
		#print(get_asset_hash("vo_full_101304-4-18_hca.hca")[0]["index"], get_asset_hash("vo_full_101304-4-18_hca.hca")[0]["assetType"])

	return response

server.run(host='0.0.0.0')