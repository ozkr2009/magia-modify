# magia-modify
## A tool that helps setup the server environment for Magia mod
* Downloads latest JSON asset list file from original server
* Creates a hash map of all the asset list files
* Downloads git repository containing modified assets
* Parses server directories and calculated MD5 hashes along with other information
* Uses the file name to look up location in the asset lists files and inserts new information
### For subsequest requests
* It checks if any files have been modified since last pull 
* Calculated Md5 and other informamtion
* Looks up location and inserts new info using hash map
