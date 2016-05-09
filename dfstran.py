#!/usr/bin/env python

from __future__ import print_function
import os
import os.path

sectorlen=2**8

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
        self.catnum=None

    def read(self):
        pass

    def read_after(self):
        pass

    def write_as_file(self, dir):
        filename_inf=open(os.path.join(dir,'.{}.{}.inf'.format(self.dir,self.name)),'w')
        filename_inf.write('{}, '.format(self.name))
        filename_inf.write('L:{:06X}, '.format(self.load_address))
        filename_inf.write('E:{:06X}, '.format(self.exec_address))
        filename_inf.write('F:{}\n'.format('L' if self.loc else ''))
        filename_inf.close()
        filename_inf2=open(os.path.join(dir,'.{}.{}.inf2'.format(self.dir,self.name)),'w')
        filename_inf2.write('Start sector:{}\n'.format(self.start_sector))
        filename_inf2.write('Length:{}\n'.format(self.len))
        filename_inf2.write('Catalogue index:{}\n'.format(self.catnum))
        filename_inf2.write('After:')
        for c in self.read_after():
            filename_inf2.write('{:02x}'.format(c))
        filename_inf2.close()
        filout=open(os.path.join(dir, '{}.{}'.format(self.dir, self.name)), 'wb')
        filout.write(self.read())
        filout.close()

    def info(self):
        '''
        Return the info line as output by a BBC Micro's *info command e.g.:
        $.FILE    L 001900 001A00 000067 02B
        '''
        return '{}.{:<7s} {} {:06X} {:06X} {:06X} bytes {:03X}'.format(self.dir, self.name, 'L' if self.loc else ' ',self.load_address, self.exec_address, self.len, self.start_sector)

    def __str__(self):
        return self.info()

class dfsdisc(object):
    def __init__(self):
        self.title=None
        self.serial_no=None
        self.sectors=None
        self.boot_options=None
        self.ssd_size=None
        self.cat=[]

    def list_catalogue(self):
        '''
        Return a the list of filenames of the format dir.leafname.

        The index number of a specific file is needed for functions like read()
        '''
        return list(map(lambda f:f.dir+'.'+f.name,self.cat))

    def list_unused_sectors(self):
        '''
        Return a list of sector numbers for unused sectors
        '''
        pass

    def read_sector(self, sector_id):
        '''
        Return the contents of the specified sector
        '''
        pass

    def read_additional(self):
        '''
        Return any extra data placed after the disc image finishes, or
        the empty string if the disc is the expected size or undersized
        '''
        pass

    def read_unused_catalogue(self):
        '''
        Return a pair of strings representing the unused space after the
        catalogue in sectors 0 and 1.
        '''
        pass

    def write_as_ssd(self, filename):
        pass #TODO

    def write_as_files(self, dir):
        if os.path.isdir(dir):
            if os.listdir(dir):
                raise RuntimeError('Directory {} exists and is not empty'.format(dir))
        else:
            if os.path.isfile(dir):
                raise RuntimeError('{} is an existing file; please provide a name for a directory into which the disc can be unpacked'.format(dir))
            else:
                os.makedirs(dir)
        disk_inf=open(os.path.join(dir,'..THIS_DISK.inf'),'w')
        disk_inf.write('*OPT4,{}\n'.format(self.boot_options))
        disk_inf.write('T: {}, S: {}\n'.format(self.title, self.serial_no))
        disk_inf.close()
        disk_inf2=open(os.path.join(dir,'..THIS_DISK.inf2'),'w')
        disk_inf2.write('Sectors:{}, '.format(self.sectors))
        disk_inf2.write('SSD file size:{}, '.format(self.ssd_size))
        disk_inf2.write('Catalogue len:{}\n'.format(len(self.cat)))
        disk_inf2.close()
        after_cat=self.read_unused_catalogue()
        empty_inf=open(os.path.join(dir,'..Empty.inf'),'w')
        empty_inf.write('After sector 000:')
        for c in after_cat[0]:
            empty_inf.write('{:02x}'.format(c))
        empty_inf.write('\n')
        empty_inf.write('After sector 001:')
        for c in after_cat[1]:
            empty_inf.write('{:02x}'.format(c))
        empty_inf.write('\n')
        for i in self.list_unused_sectors():
            empty_inf.write('Sector {:03X}:'.format(i))
            for c in self.read_sector(i):
                empty_inf.write('{:02x}'.format(c))
            empty_inf.write('\n')
        empty_inf.close()
        for fil in self.cat:
            fil.write_as_file(dir)

    def write_as_adfs(self, dir):
        pass #TODO


class ssdfile(dfsfile):
    def __init__(self, ssddisc, catnum):
        self.ssddisc=ssddisc
        super(ssdfile, self).__init__()
        self.readcat(catnum)

    def readcat(self, catnum):
        self.catnum=catnum
        nameblock=self.ssddisc.read_sector(0)[catnum*8+8:catnum*8+16]
        attribblock=self.ssddisc.read_sector(1)[catnum*8+8:catnum*8+16]
        self.dir=chr(nameblock[-1] & 0x7f)
        self.loc=(nameblock[-1] & 0x80) >> 7
        self.name=nameblock[0:7].decode(encoding='Latin1').rstrip()
        load=attribblock[0] + (attribblock[1] << 8)
        execute=attribblock[2] + (attribblock[3] << 8)
        self.len=attribblock[4] + (attribblock[5] << 8) + ((attribblock[6] & 0x30) << 12)
        self.start_sector=attribblock[7] + ((attribblock[6] & 0x03) << 8)
        exec_extra=(attribblock[6] & 0xc0) >> 6
        if exec_extra==0x03:
          exec_extra=0xff
        self.exec_address=execute+(exec_extra<<16)
        load_extra=(attribblock[6] & 0x0c) >> 2
        if load_extra==0x03:
          load_extra=0xff
        self.load_address=load+(load_extra<<16)

    def read(self):
        return self.ssddisc.read(self.start_sector, self.len)

    def read_after(self):
        if self.len % sectorlen == 0:
            return b''
        sectordata=self.ssddisc.read_sector(self.start_sector+int(self.len / sectorlen))
        return sectordata[self.len % sectorlen:]

class ssddisc(dfsdisc):
    def __init__(self, filename):
        super(ssddisc, self).__init__()
        self.file=open(filename,'rb')
        self.readcat()

    def readcat(self):
        self.file.seek(0)
        namesector=self.file.read(sectorlen)
        attribsector=self.file.read(sectorlen)
        self.title=(namesector[0:7]+attribsector[0:3]).decode().rstrip()
        self.serial_no=attribsector[4]
        catlen=attribsector[5]&0xfc
        self.sectors=attribsector[7]+((attribsector[6]&0x07) << 8)
        self.boot_options=attribsector[6]&0xf0 >> 4
        self.ssd_size=self.file.seek(0,2)
        self.cat=[]
        for i in range(int(catlen/8)):
            f=ssdfile(self, i)
            self.cat.append(f)

    def read(self, start_sector, length):
        self.file.seek(start_sector*sectorlen)
        return self.file.read(length)

    def list_unused_sectors(self):
        ordered=sorted(self.cat,key=lambda fil:fil.start_sector)
        end=1 # End of the catalogue
        s=[]
        for i in range(len(ordered)):
            s=s+list(range(end+1,ordered[i].start_sector))
            end=ordered[i].start_sector+int(ordered[i].len / sectorlen)
            if ordered[i].len % sectorlen == 0:
                end-=1
        s=s+list(range(end+1,self.sectors))
        return s

    def read_sector(self, sector):
        self.file.seek(sector*sectorlen)
        return self.file.read(sectorlen)

    def read_additional(self):
        self.file.seek(self.sectors*sectorlen)
        return self.file.read()

    def read_unused_catalogue(self):
        self.file.seek(len(self.cat)*8+8)
        u=[self.file.read(sectorlen-8-len(self.cat)*8)]
        self.file.seek(len(self.cat)*8+sectorlen+8)
        u.append(self.file.read(sectorlen-8-len(self.cat)*8))
        return u


d=ssddisc('./Test.ssd')
print('DEBUG: Disc title:', d.title)
print('DEBUG: Serial number:', hex(d.serial_no))
print('DEBUG: Sectors:', d.sectors)
print('DEBUG: Boot options:', d.boot_options)
if d.ssd_size != d.sectors * sectorlen:
    print('DEBUG: Actual size {} sectors {}'.format(int(d.ssd_size/sectorlen),'with {} extra byte(s)'.format(d.ssd_size % sectorlen) if d.ssd_size % sectorlen != 0 else ''))
i=0
for f in d.cat:
    print('DEBUG: Cat {}: {}'.format( i+1,f.info() ))
    i+=1

f=[f for f in d.cat if f.name=='!BOOT'][0]
print('DEBUG:',f.read())
print('DEBUG len:',len(f.read_after()))
print('DEBUG unused sectors:',list( map(lambda s:hex(s),d.list_unused_sectors()) ))
print('DEBUG additional:',d.read_additional())
u=d.read_unused_catalogue()
if len(u[0]) != 208 or len(u[0]) != len(u[1]):
    print('DEBUG FAIL unused catalogue len:', len(u[0]), len(u[1]))
elif u[0][0] != 0x10 and u[0][-1] != 0x01:
    print('DEBUG FAIL unused catalogue sector 0', u[0][0], u[0][-1])
elif u[1][0] != 0xf0 and u[1][-1] != 0x0f:
    print('DEBUG FAIL unused catalogue sector 1', u[1][0], u[1][-1])
else:
    print('DEBUG unused catalogue: OK')
d.write_as_files('unpackd')
