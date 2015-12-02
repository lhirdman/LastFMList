#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import sys
import httplib2 as http
import json
import os
from datetime import datetime
import time
import sqlite3 as lite

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

con = None

def insert_data( songid, artist, title, album, playdate, image ):
  #  notice = (title, message, image)
    print songid + " - " + artist + " - " + title + " - " + album + " - " + playdate
    return

def init_db():
    try:
        con = lite.connect('mylist.db')
        cur = con.cursor()
        cur.execute('DROP TABLE IF EXISTS playlist')
        cur.execute('CREATE TABLE playlist(artist TEXT, title TEXT, album TEXT, playdate TEXT, image BLOB)')
        con.commit()
    except lite.Error, e:
        if con:
            con.rollback()
        print "Error %s: " % e.args[0]
        sys.exit(1)

def get_data( user ):
    headers = {
       'Accept': 'application/json',
       'Content-Type': 'application/json; charset=UTF-8'
    }
    api_key="ccfcd6b800861bf2057516f1bc09ebb2"
    lmethod="user.getrecenttracks"
    limit="5"
    uri="http://ws.audioscrobbler.com"
    path="/2.0/?method=" + lmethod + "&limit=" + limit + "&user=" + user + "&api_key=" + api_key + "&format=json"
    target = urlparse(uri+path)
    method='GET'
    body=''
    h = http.Http()
    try:
        response, content = h.request(
            target.geturl(),
            method,
            body,
            headers)
    except http.HttpLib2Error:
        print "ResponseNotReady Error"
        return ( {'error': '3'} )
    if ( response.status==200 ):
      data = json.loads(content)
    else:
      print response.status
      data = { 'mystatus': response.status }
    return data

def strip_it( data ):
    if ( data.has_key('recenttracks') ):
        mydata = data['recenttracks']
    else:
        print "Track info not found"
        return ( {'error': '1'} )
        time.sleep(10)
    if ( mydata.has_key('track') ):
        try:
            data = data['recenttracks']['track'][0]
        except:
            print "failed to get data"
    else:
        print "Track info not found"
        return ( {'error': '2'} )
    track = data['name']
    artist = data['artist']['#text']
    album = data['album']['#text']
    image = data['image'][1]['#text']
    if ( data.has_key('date') ):
        playtime = data['date']['#text']
    else:
        playtime = time.asctime( time.localtime(time.time()) )
    songid = data['mbid']
    mylist = {
        'track': track,
        'artist':  artist,
        'image': image,
        'pdate': playtime,
        'songid': songid,
        'album': album
    }
    return mylist

def get_image( uri ):
   method = 'GET'
   h = http.Http()
   target = urlparse(uri)
   body = ''
   response, content = h.request(
        target.geturl(),
        method)
   lmfile = open("/tmp/cover.png", "wb")
   lmfile.write(content);
   lmfile.close()
   imgpath = "file:///tmp/cover.png"
   return imgpath

if len(sys.argv) == 1:
    print "usage: " + sys.argv[0] + " your_lastfm_username"
    sys.exit(1)

user = sys.argv[1]
oldTrackId = 'xxx'
oldTrackName = 'xxx'
oldImgPath = 'xxx'
oldPDate = '17 Jul 1975, 10:11'
cnt = 0
while 1:
    data = get_data( user );
    if ( data.has_key('mystatus') ):
        continue
    elif ( data.has_key('error') ):
        continue
    mylist = strip_it( data );
    if ( mylist.has_key('error') ):
        print "Error occured: " + mylist['error']
        continue
    if ( mylist['songid'] == '' ):
        if ( mylist['track'] == oldTrackName ):
            cnt = cnt + 1
            if ( cnt >= 60 ):
                time.sleep(300)
                cnt = 0
            else:
                time.sleep(10)
            continue
    elif ( mylist['songid'] == oldTrackId ):
        if ( cnt >= 60 ):
            time.sleep(300)
            cnt = 0
        else:
            time.sleep(10)
        continue
    elif ( mylist['pdate'] <= oldPDate ):
        print "Old song returned"
        if ( cnt >= 60 ):
            time.sleep(300)
            cnt = 0
        else:
            time.sleep(10)
        continue

    # print "New track id: " + mylist['songid']
    oldTrackId = mylist['songid']
    oldTrackName = mylist['track']
    oldPDate = mylist['pdate']
    if ( mylist['image'] == oldImgPath ):
        print "No new image needed"
    else:
        if ( mylist['image'] != '' ):
            imgpath = get_image( mylist['image'] );
            oldImgPath = mylist['image']
        else:
            imgpath = 'dialog-question'
    insert_data( mylist['songid'], mylist['artist'], mylist['track'], mylist['album'], mylist['pdate'], imgpath );
    time.sleep(10)
