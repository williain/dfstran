#!/usr/bin/env python

from __future__ import print_function
import os
import os.path
import argparse

import unittest

sectorlen=2**8

class DfsFile(object):
    '''
    DfsFile represents one file on a DFS disc
    '''
    def __init__(self):
        self.name=None
        self.dir=None
        self.loc=None
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
        filename_inf.write('{}.{}, '.format(self.dir, self.name))
        filename_inf.write('L:{:06X}, '.format(self.load_address))
        filename_inf.write('E:{:06X} '.format(self.exec_address))
        filename_inf.write('F:{}\n'.format('L' if self.loc else ''))
        filename_inf.close()
        filename_inf2=open(os.path.join(dir,'.{}.{}.inf2'.format(self.dir,self.name)),'w')
        filename_inf2.write('Start sector:{}\n'.format(self.start_sector))
        filename_inf2.write('Length:{}\n'.format(self.len))
        filename_inf2.write('Catalogue index:{}\n'.format(self.catnum))
        filename_inf2.write('After:')
        for c in self.read_after():
            filename_inf2.write('{:02x}'.format(ord(c)))
        filename_inf2.close()
        filout=open(os.path.join(dir, '{}.{}'.format(self.dir, self.name)), 'wb')
        filout.write(self.read())
        filout.close()

    def info(self):
        '''
        Return the info line as output by a BBC Micro's *info command e.g.:
        $.FILE    L 001900 001A00 000067 02B
        '''
        return '{}.{:<7s} {} {:06X} {:06X} {:06X} {:03X}'.format(self.dir, self.name, 'L' if self.loc else ' ',self.load_address, self.exec_address, self.len, self.start_sector)

    def __str__(self):
        return self.info()

class TestDfsFile(unittest.TestCase):
    def setUp(self):
        self.f=DfsFile()
        self.f.dir='T'
        self.f.name='estfile'
        self.f.loc=True
        self.f.load_address=0x1000
        self.f.exec_address=0x1100
        self.f.len=0x1d0
        self.f.catnum=2
        self.f.start_sector=0x040
        self.f.read=lambda:'Pass'.encode(encoding='Latin_1')
        self.f.read_after=lambda:['\xde','\xad','\xbe','\xef']

    def test_info(self):
        self.assertEqual(self.f.info(),'T.estfile L 001000 001100 0001D0 040')

    def test_write_as_file(self):
        self.assertEqual(os.mkdir(os.path.join('test_data','test_out')), None)
        try:
            self.f.write_as_file(os.path.join('test_data','test_out'))
            with open(os.path.join('test_data','test_out','.T.estfile.inf')) as f:
                self.assertEqual(f.read(),'T.estfile, L:001000, E:001100 F:L\n')
            self.assertEqual(os.unlink(os.path.join('test_data','test_out','.T.estfile.inf')), None)
            with open(os.path.join('test_data','test_out','.T.estfile.inf2')) as f:
                self.assertEqual(f.read(),'Start sector:64\nLength:464\nCatalogue index:2\nAfter:deadbeef')
            self.assertEqual(os.unlink(os.path.join('test_data','test_out','.T.estfile.inf2')), None)
            with open(os.path.join('test_data','test_out','T.estfile')) as f:
                self.assertEqual(f.read(),'Pass')
            self.assertEqual(os.unlink(os.path.join('test_data','test_out','T.estfile')), None)
        finally:
            for f in os.listdir(os.path.join('test_data','test_out')):
                os.unlink(os.path.join('test_data','test_out',f))
            os.rmdir(os.path.join('test_data','test_out'))

class DfsDisc(object):
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
            empty_inf.write('{:02x}'.format(ord(c)))
        empty_inf.write('\n')
        empty_inf.write('After sector 001:')
        for c in after_cat[1]:
            empty_inf.write('{:02x}'.format(ord(c)))
        empty_inf.write('\n')
        for i in self.list_unused_sectors():
            empty_inf.write('Sector {:03X}:'.format(i))
            for c in self.read_sector(i):
                empty_inf.write('{:02x}'.format(ord(c)))
            empty_inf.write('\n')
        empty_inf.close()
        for fil in self.cat:
            fil.write_as_file(dir)

    def write_as_adfs(self, dir):
        pass #TODO


class SsdFile(DfsFile):
    def __init__(self, ssddisc, catnum):
        self.ssddisc=ssddisc
        super(SsdFile, self).__init__()
        self.readcat(catnum)

    def readcat(self, catnum):
        self.catnum=catnum
        nameblock=self.ssddisc.read_sector(0)[catnum*8+8:catnum*8+16]
        attribblock=self.ssddisc.read_sector(1)[catnum*8+8:catnum*8+16]
        self.dir=chr(ord(nameblock[-1]) & 0x7f)
        self.loc=(ord(nameblock[-1]) & 0x80) >> 7
        self.name=nameblock[0:7].rstrip()
        load_address=ord(attribblock[0]) + (ord(attribblock[1]) << 8)
        exec_address=ord(attribblock[2]) + (ord(attribblock[3]) << 8)
        self.len=ord(attribblock[4]) + (ord(attribblock[5]) << 8) + ((ord(attribblock[6]) & 0x30) << 12)
        self.start_sector=ord(attribblock[7]) + ((ord(attribblock[6]) & 0x03) << 8)
        exec_extra=(ord(attribblock[6]) & 0xc0) >> 6
        if exec_extra==0x03:
          exec_extra=0xff
        self.exec_address=exec_address+(exec_extra<<16)
        load_extra=(ord(attribblock[6]) & 0x0c) >> 2
        if load_extra==0x03:
          load_extra=0xff
        self.load_address=load_address+(load_extra<<16)

    def read(self):
        return self.ssddisc.read(self.start_sector, self.len)

    def read_after(self):
        if self.len % sectorlen == 0:
            return b''
        sectordata=self.ssddisc.read_sector(self.start_sector+int(self.len / sectorlen))
        return sectordata[self.len % sectorlen:]

class SsdDisc(DfsDisc):
    def __init__(self, filename):
        super(SsdDisc, self).__init__()
        self.file=open(filename,'rb')
        self.readcat()

    def __del__(self):
        if hasattr(self, 'file'):
            self.file.close()

    def readcat(self):
        self.file.seek(0)
        namesector=self.file.read(sectorlen).decode(encoding='Latin1')
        attribsector=self.file.read(sectorlen).decode(encoding='Latin1')
        self.title=(namesector[0:7]+attribsector[0:3]).rstrip()
        self.serial_no=ord(attribsector[4])
        catlen=ord(attribsector[5])&0xfc
        self.sectors=ord(attribsector[7])+((ord(attribsector[6])&0x07) << 8)
        self.boot_options=(ord(attribsector[6])&0xf0) >> 4
        self.file.seek(0,2)
        self.ssd_size=self.file.tell()
        self.cat=[]
        for i in range(int(catlen/8)):
            f=SsdFile(self, i)
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
        return self.file.read(sectorlen).decode(encoding='Latin1')

    def read_additional(self):
        self.file.seek(self.sectors*sectorlen)
        return self.file.read().decode(encoding='Latin1')

    def read_unused_catalogue(self):
        self.file.seek(len(self.cat)*8+8)
        u=[self.file.read(sectorlen-8-len(self.cat)*8).decode(
          encoding='Latin1'
        )]
        self.file.seek(len(self.cat)*8+sectorlen+8)
        u.append(self.file.read(sectorlen-8-len(self.cat)*8).decode(
          encoding='Latin1'
        ))
        return u

    def output_bin(self, heading, data):
        r=heading+' '*((0-len(heading.split('\n')[-1])) % 5)
        if len(data)==0:
            r+='None'
        while len(data)>1:
            r+='{:02x}{:02x} '.format(ord(data[0]),ord(data[1]))
            data=data[2:]
        if len(data)==1:
            r+='{:02x}'.format(ord(data[0]))
        return r

    def info(self, verbose):
        if verbose:
            r='Title: {}\nSerial no:{}\n'
        else:
            r='{} ({})\n'
        r=r.format(self.title,self.serial_no)
        if verbose:
            k=self.sectors*sectorlen/1024
            r+='Total sectors:0x{:03x} ({}K)\n'.format(
              self.sectors, int(k) if int(k) == k else k # Tidy py3 fractions
            )
        if verbose>1:
            if self.ssd_size != self.sectors * sectorlen:
                r+='INFO: Actual size 0x{:03x} sectors{}\n'.format(
                  self.ssd_size//sectorlen,
                  ' with {} extra byte(s)'.format(self.ssd_size % sectorlen)
                    if self.ssd_size % sectorlen != 0 else ''
                )
        opt4=['off','LOAD','RUN','EXEC']+['invalid']*12
        r+='Option {} ({})\n'.format(
          self.boot_options, opt4[self.boot_options]
        )
        cat=self.cat
        if not verbose:
            cat=sorted(cat,key=lambda fil:fil.dir+'.'+fil.name)
        i=0
        for f in cat:
            if verbose:
                r+='File {}: {}{}\n'.format(
                  i+1, f.info(),
                  ' cropped!'
                    if f.start_sector*sectorlen+f.len > self.ssd_size
                    else
                  ''
                )
                if verbose>2:
                    r+=self.output_bin('Additional data: ', f.read_after())+'\n'
            else:
                r+=f.info()+'\n'
            i+=1
        if verbose>2:
            u=self.read_unused_catalogue()
            r+=self.output_bin('Unused in sector 0x000: ', u[0])+'\n'
            r+=self.output_bin('Unused in sector 0x001: ' ,u[1])+'\n'
        if verbose>1:
            u=self.list_unused_sectors()
            if len(u)==0:
                r+='All sectors are in use'
            else:
                r+='Unused sectors:'
                for s in u:
                    if (s*sectorlen) >= self.ssd_size:
                        break
                    if verbose>2:
                        r+=self.output_bin(
                          '\n- Sector 0x{:03x}: '.format(s),
                          self.read_sector(s)
                        )
                    else:
                        r+='0x{:03x} '.format(s)
                if self.sectors > self.ssd_size//sectorlen:
                    r+='\nSector'
                    if self.ssd_size//sectorlen+1 >= self.sectors:
                        r+=' 0x{:03x} cropped'.format(self.sectors)
                    else:
                        r+='s 0x{:03x}-0x{:03x} cropped'.format(
                          -(-self.ssd_size//sectorlen),
                          self.sectors
                        )
                r+='\n'
        if verbose>2:
            a=self.read_additional()
            if a:
                r+=self.output_bin('Data after disc image: ',a)+'\n'
            else:
                r+='No data after disc image\n'
        return r

class TestSsdDisc(unittest.TestCase):
    def setUp(self):
        self.d=SsdDisc('./test_data/Test1.ssd')

    def test_disc(self):
        self.assertEqual(self.d.title, 'TEST')
        self.assertEqual(self.d.serial_no, 0x11)
        self.assertEqual(self.d.sectors, 56)
        self.assertEqual(self.d.boot_options, 3)
        self.assertEqual(self.d.ssd_size % sectorlen, 1)

    def test_file(self):
        f=[f for f in self.d.cat if f.name=='!BOOT'][0]
        self.assertEqual(len(f.read()), 14)
        self.assertEqual(len(f.read_after()), 242)

    def test_list_unused_sectors(self):
        self.assertEqual(len(self.d.list_unused_sectors()), 1)
        self.assertEqual(self.d.list_unused_sectors()[0], 0x28)

    def test_read_additional(self):
        self.assertEqual(len(self.d.read_additional()), 1)
        self.assertEqual(ord(self.d.read_additional()[0]), 0x00)

    def test_read_unused_catalogue(self):
        u=self.d.read_unused_catalogue()
        self.assertEqual(len(u[0]), 208)
        self.assertEqual(len(u[1]), 208)
        self.assertEqual(ord(u[0][0]), 0x10)
        self.assertEqual(ord(u[0][-1]), 0x01)
        self.assertEqual(ord(u[1][0]), 0xf0)
        self.assertEqual(ord(u[1][-1]), 0x0f)

if __name__ == '__main__':
    pars=argparse.ArgumentParser(prog='dfstran', description='pack and unpack BBC Micro DFS disc images')
    pars.add_argument('--verbose', '-v', action='count', help='Report more details of the input')
    pars.add_argument('input', help='The ssd file or directory to be processed')
    pars.add_argument('output', nargs='?', help='The target file or folder for the input to be converted into')
    pars.add_argument('--cat', '-c', action='store_true', help='List the contents of the input; do not convert')
    args=pars.parse_args()
    if not os.path.exists(args.input):
        print("ERROR: Input '{}' doesn't exist".format(args.input))
        exit(2)
    else:
        d=SsdDisc(args.input)

    verbose=args.verbose
    if verbose==None:
        verbose=0
    if args.cat:
        if args.output!=None:
            print('WARNING: Output given with --cat option; not converting')
        print(d.info(verbose), end='')
    else:
        if args.output==None:
            print('INFO: No output given; cataloging input')
            print(d.info(verbose), end='')
        if args.output!=None:
            if verbose>1:
                print(d.info(verbose-2), end='')
            d.write_as_files(args.output)
            if verbose:
                print('INFO: {} unpacked to {}'.format(
                  args.input, args.output
                ))
