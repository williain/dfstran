#!/usr/bin/env python

from __future__ import print_function

sectorlen=2**8
files=[] # Assume space for 31 entries

class dfsfile(object):
    '''
    dfsfile represents one file on a DFS disc
    '''
    def __init__(self):
        self.name=None
        self.dir=None
        self.load_address=None
        self.exec_address=None
        self.len=None
        self.start_sector=None

    def __str__(self):
        return '{}.{:<7s} {} {:06X} {:06X} {:06X} bytes {:03X}'.format(self.dir, self.name, 'L' if self.loc else ' ',self.load_address, self.exec_address, self.len, self.start_sector)

class dfsfree(object):
    '''
    dfsfree represents all the free space on a DFS disc
    '''
    def __init__(self):
        self.sectors=[]
        self.afterdisc=None

class dfsdisc(object):
    def __init__(self):
        self.title=None
        self.serial_no=None
        self.sectors=None
        self.boot_options=None
        self.ssd_size=None #TODO Do we need this if we've got a file cat and the free space?
        self.cat=[]
        self.free=dfsfree()
        #TODO Truncated?

    def list_catalogue(self):
        '''
        Return a the list of filenames of the format dir.leafname.

        The index number of a specific file is needed for functions like read()
        '''
        return list(map(lambda f:f.dir+'.'+f.name,self.cat))

    def info(self, file_id):
        '''
        Return the info string for the specified id
        '''
        return str(self.cat[file_id])

    def read(self, file_id):
        '''
        Return the file contents for the specified id
        '''
        pass

    def write_as_ssd(self, filename):
        pass #TODO

    def write_as_files(self, dir):
        pass #TODO

    def write_as_adfs(self, dir):
        pass #TODO

class ssddisc(dfsdisc):
    def __init__(self, filename):
        self.file=open(filename,'rb')

    def trunc_space(self,string):
        try:
            return string[0:string.index(' ')]
        except ValueError:
            return string # No space ending found

    def readcat(self):
        self.file.seek(0)
        namesector=self.file.read(sectorlen)
        attribsector=self.file.read(sectorlen)
        self.title=self.trunc_space(
          (namesector[0:7]+attribsector[0:3]).decode()
        )
        self.serial_no=attribsector[4]
        catlen=attribsector[5]&0xfc
        self.sectors=attribsector[7]+((attribsector[6]&0x07) << 8)
        self.boot_options=attribsector[6]&0xf0 >> 4
        self.ssd_size=self.file.seek(0,2)
        self.cat=[]
        for i in range(8,catlen+1,8):
            f=dfsfile()
            nameblock=namesector[i:i+8]
            f.dir=chr(nameblock[-1] & 0x7f)
            f.loc=(nameblock[-1] & 0x80) >> 7
            f.name=self.trunc_space( nameblock[0:7].decode(encoding='Latin1') )
            load=attribsector[i] + (attribsector[i+1] << 8)
            execute=attribsector[i+2] + (attribsector[i+3] << 8)
            f.len=attribsector[i+4] + (attribsector[i+5] << 8) + ((attribsector[i+6] & 0x30) << 12)
            f.start_sector=attribsector[i+7] + ((attribsector[i+6] & 0x03) << 8)
            exec_extra=(attribsector[i+6] & 0xc0) >> 6
            if exec_extra==0x03:
              exec_extra=0xff
            f.exec_address=execute+(exec_extra<<16)
            load_extra=(attribsector[i+6] & 0x0c) >> 2
            if load_extra==0x03:
              load_extra=0xff
            f.load_address=load+(load_extra<<16)
            self.cat.append(f)

    def read(self, file_id):
        self.file.seek(self.cat[file_id].start_sector<<8)
        return self.file.read(self.cat[file_id].len)


d=ssddisc('./Test.ssd')
d.readcat()
print('DEBUG: Disc title:', d.title)
print('DEBUG: Serial number:', hex(d.serial_no))
print('DEBUG: Sectors:', d.sectors)
print('DEBUG: Boot options:', d.boot_options)
if d.ssd_size != d.sectors<<8:
    print('DEBUG: Actual size:',d.ssd_size>>8, 'sectors','with '+str(d.ssd_size%256)+' extra byte(s)' if d.ssd_size%256 else '')
print('DEBUG: Cat',d.list_catalogue())
for i in range(len( d.list_catalogue() )):
    print('DEBUG: Cat {}: {}'.format( i+1,d.info(i) ))

print('DEBUG:',d.read(d.list_catalogue().index('$.!BOOT')))
