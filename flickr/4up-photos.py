#!/usr/bin/env python

import sys
import datetime
import logging
import json
import csv
import os.path

import optparse
import ConfigParser
import Flickr.API
    
if __name__ == '__main__' :

    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="config", help="path to an ini config file")
    parser.add_option("-u", "--user-id", dest="user_id", help="the user to fetch photos for")
    parser.add_option("-o", "--outdir", dest="outdir", help="where to write data files")
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False, help='be chatty (default is false)')

    (opts, args) = parser.parse_args()        

    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    cfg = ConfigParser.ConfigParser()
    cfg.read(opts.config)

    api_key=cfg.get('flickr', 'api_key')
    api_secret=cfg.get('flickr', 'api_secret')
    auth_token=cfg.get('flickr', 'auth_token')
    
    api = Flickr.API.API(api_key, api_secret)

    # sudo put me in a library or something...
    # (20130930/straup)

    if opts.user_id == 'me':
        
        args = {
            'method': 'flickr.auth.checkToken',
            'format': 'json',
            'nojsoncallback': 1,
            'auth_token': auth_token
            }

        req = Flickr.API.Request(**args)
        res = api.execute_request(req)

        data = json.loads(res.read())
        opts.user_id = data['auth']['user']['nsid']

    pages = None
    page = 1

    current_year = None
    writer = None

    while not pages or page <= pages:

        print "page %s (%s)" % (page, pages)

        args = {
            'method':'flickr.photos.search',
            'user_id':opts.user_id,
            'format':'json',
            'nojsoncallback':1,
            'extras':'date_taken,date_upload,owner_name,geo,date_taken,url_m,url_n,url_c,url_l',
            'auth_token':auth_token,
            'page':page,
            'sort':'date-posted-asc'
            }

        req = Flickr.API.Request(**args)
        res = api.execute_request(req)
        
        data = json.loads(res.read())

        if not pages:
            pages = data['photos']['pages']

        print "page %s: %s photos" % (current_year, len(data['photos']['photo']))

        for ph in data['photos']['photo']:

            # print ph

            # du = ph['dateupload']
            # du = datetime.date.fromtimestamp(du)
            # year_upload = du.year
            
            dt = ph['datetaken']
            dt = dt.split('-')
            year_taken = dt[0]
            
            ymd = ph['datetaken'].split(' ')
            ymd = ymd[0]
            
            title = ph['title']
            owner = ph['ownername']
            
            full_img = None
            
            for url in ('url_l', 'url_c', 'url_m'):

                if ph.get(url):
                    full_img = ph[url]
                    break

            logging.debug("full_img is %s" % full_img)

            photo_page = "http://www.flickr.com/photos/%s/%s" % (ph['owner'], ph['id'])

            desc = ""
        
            if title != '':
                desc = "%s (%s)" % (title, ymd)
            else:
                desc = "(%s)" % ymd

            meta = json.dumps({
                    'og:description': desc,
                    'pinterestapp:source': photo_page,
                    })

            row = {
                'full_img': full_img,
                'id': ph['id'],
                'meta': meta,
                }

            logging.debug(row)

            if not current_year or year_taken != current_year:

                current_year = year_taken
                fname = "flickr-photos-%s.csv" % current_year

                path = os.path.join(opts.outdir, fname)

            if os.path.exists(path):

                logging.debug("append row to %s" % path)

                fh = open(path, 'a')
                writer = csv.DictWriter(fh, fieldnames=('full_img', 'id', 'meta'))

            else:

                logging.debug("write row %s" % path)

                fh = open(path, 'w')

                writer = csv.DictWriter(fh, fieldnames=('full_img', 'id', 'meta'))
                writer.writeheader()

            writer.writerow(row)

        page += 1

    logging.info("done")
    sys.exit()
