# fdroid-dl
Is a python based f-droid mirror generation and update utility. Point at one or more existing f-droid repositories and the utility will download the metadata (pictures, descriptions,..) for you and place it in your local system. Simply run ```fdroid-dl && fdroid update``` and you are set.

## Motivation
The idea is to have an no internet local copy of one or more repositories, without the need to compile the thousands of apps on your own build server but rather download them like the android client does. So this tool came into existence to simply download a while repository and import the apps into your own locally installed one. At the time of writing a full offline copy including assets is ~7.5GB of the official repository of f-droid.org.

# Installation
fdroid-dl is available via pip, simply run ```pip install fdroid-dl``` and you can use ```fdroid-dl``` on your command line.

# Command Line Options

# Configuration File

# TODO
- [x] Create backend to crawl existing repos
- [x] Fetch info directly index.jar and index-v1.jar
- [x] Compatibility with old and new repo styles
- [x] Download multi threaded
- [x] Verify apk checksum
- [x] Local cache for index files
- [ ] Source code download not implemented yet
- [ ] Metadata update to do delta not full download all the time
- [ ] Cleanup strategy for old apk files (maybe ```fdroid update``` does this already?)
- [ ] Create a CLI [python click](http://click.pocoo.org/5/)
- [ ] pip package [packaging.python.org](https://packaging.python.org/tutorials/packaging-projects/)
- [ ] CI builds for pip package
- [ ] Documentation ;-)
- [ ] Writing tests [pytest](https://docs.pytest.org/en/latest/)

# CHANGELOG
- WIP: Documentation added
- WIP: Test added

# Development
## Requirements
* python 3.x
* pip 3.x
* virtualenv 3.x

## install locally
```
# git clone https://github.com/t4skforce/fdroid-dl.git
# cd fdroid-dl
# virtualenv .env
# source .env/bin/activate
# python setup.py install
# fdroid-dl --help
```

### References
While this project was developed the following references where used

#### F-Droid
* Setup an F-Droid App Repo [f-droid.org](https://f-droid.org/en/docs/Setup_an_F-Droid_App_Repo/)
* Build Metadata Reference [f-droid.org](https://f-droid.org/en/docs/Build_Metadata_Reference/)
* All About Descriptions, Graphics, and Screenshots [f-droid.org](https://f-droid.org/en/docs/All_About_Descriptions_Graphics_and_Screenshots/)
* How to Add a Repo to F-Droid [f-droid.org](https://f-droid.org/en/tutorials/add-repo/)
* How to Send and Receive Apps Offline [f-droid.org](https://f-droid.org/en/tutorials/swap/)

#### Python
* Python Documentation [python.org](https://docs.python.org/3/)
* PyYAML Documentation [pyyaml.org](https://pyyaml.org/wiki/PyYAMLDocumentation)
* Requests: HTTP for Humans [python-requests.org](http://docs.python-requests.org/en/master/)
  * Suppress InsecureRequestWarning: Unverified HTTPS request is being made in Python2.6  [stackoverflow.com](https://stackoverflow.com/questions/27981545/suppress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho)
  * How to download large file in python with requests.py? [stackoverflow.com](https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py)
* Asynchronous Python HTTP Requests for Humans using Futures [requests-futures](https://github.com/ross/requests-futures)
* Testing Your Code [python-guide.org](https://docs.python-guide.org/writing/tests/)
