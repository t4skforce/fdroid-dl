#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
    def repo(self):
        with Downloader(threads=self.config.threads) as d:
            downloads = {}
            for repo in self.config.repos:
                try:
                    if not 'error' in repo: # ignore repos with download error
                        for appselector in repo.apps:
                            for appid in repo.index.findAppIds(appselector):
                                packages = repo.index.get('packages',{}).get(appid,[])
                                if not appid in downloads: downloads[appid]=[]
                                for pkg in packages:
                                    if not pkg.get('apkName') is None and not pkg.get('hash') is None and not pkg.get('hashType') is None:
                                        downloads[appid].append(pkg)
                except Exception as e:
                    logger.error("error processing repo metadata",e)
            for appid in downloads.keys():
                packages = sorted(downloads[appid], key=lambda e:e.get('versionCode',0), reverse=True)
                for idx,pkg in enumerate(packages):
                    if idx >= self.config.versions: break;
                    filename = os.path.basename(str(urlparse(pkg.get('apkName')).path))
                    #filename = "%s_%s.apk"%(appid,pkg.get('versionCode',pkg.get('versionName')))
                    filepath=os.path.join(self.config.repo_dir,filename)
                    if not os.path.exists(filepath):
                        d.add(pkg.get('apkName'), filename=filepath[:-4]+'.tmp', ref=pkg ,cached=repo.hash)

            for result,pkg in d.results():
                (dl_url,filename,hash,bytes,hbytes) = result
                logger.info("downloaded %s (%s) ✔"%(filename,hbytes))
                file_hash = self.__hash_file(filename,pkg.get('hashType'))
                if file_hash == pkg.get('hash'):
                    logger.info("hash verified %s (%s) ✔"%(filename,hbytes))
                    os.rename(filename,filename[:-4]+'.apk')
                else:
                    if os.path.isfile(filename): os.remove(filename)
                    logger.warn("removed %s (%s) hash verification failed ❌"%(filename,hbytes))

            if self.config.src_download == True:
                for appid in downloads.keys():
                    packages = sorted(downloads[appid], key=lambda e:e.get('versionCode',0), reverse=True)
                    for idx,pkg in enumerate(packages):
                        if idx >= self.config.versions: break;
                        if not pkg.get('srcname') is None:
                            filename = os.path.basename(urlparse(pkg.get('srcname')).path)
                            filepath=os.path.join(self.config.repo_dir,filename)
                            if not os.path.exists(filepath):
                                d.add(pkg.get('srcname'), filename=filepath, ref=pkg ,cached=repo.hash)
                for result,pkg in d.results():
                    (dl_url,filename,hash,bytes,hbytes) = result
                    logger.info("downloaded %s (%s) ✔"%(filename,hbytes))


        return self
'''
