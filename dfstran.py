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
        self.load_address=0x001900
        self.exec_address=0x001900
        self.loc=False
        self.start_sector=2
        self.len=None
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
        filename_inf2.write('Start sector:{:03x}\n'.format(self.start_sector))
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
                self.assertEqual(f.read(),'Start sector:040\nLength:464\nCatalogue index:2\nAfter:deadbeef')
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
        self.additional=None

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
        return self.additional

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
        disk_inf2.write('Sectors:{:03x}, '.format(self.sectors))
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
        empty_inf.write('After disc image:')
        for c in self.read_additional():
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

class ParseUtils(object):
    def __init__(self,directory,verbose):
        self.dir=directory
        self.verbose=verbose

    def hex2int(self, number):
        try:
            return int(number,16)
        except ValueError:
            if self.verbose:
                print('Warning: Not a hex number: {}'.format(number))
            return 0

    def str2int(self, string):
        try:
            return int(string)
        except ValueError:
            if self.verbose:
                print('Warning: Not a decimal number: {}'.format(string))
            return 0

    def text2bin(self, value, message):
        data=[]
        while len(value)>=2:
            data.append(self.hex2int(value[0:2]))
            value=value[2:]
        if len(value)==1:
            if self.verbose:
                print(message, 'has odd length; wiping last byte')
            data.append(0)
        return data

    def line(self,line,keys,filename):
        for arg in line.split(','):
            try:
                parm=arg[:arg.index(':')].strip()
                value=arg[arg.index(':')+1:].strip()
                if parm in keys.keys():
                    keys[parm](value)
                else:
                    if self.verbose:
                        print("Warning: Unrecognised parameter '{}' "+
                          "in {}".format(parm, filename)
                        )
            except ValueError:
                if self.verbose:
                    print("Warning: Malformed line '{}' in {}".format(
                      line, filename
                    ))

    def file(self, keys, filename):
        with open(os.path.join(self.dir,filename),'r') as handle:
            for l in handle.readlines():
                self.line(l.rstrip('\n'), keys, filename)

class DirFile(DfsFile):
    def __init__(self, directory, filename, get_sector, set_sector, verbose):
        super(DirFile, self).__init__()
        self.dir=directory
        self.filename=filename
        self.verbose=verbose
        self.after=[]
        self.get_sector=get_sector
        self.set_sector=set_sector
        self.parse_file()

    def parse_file(self):
        parse=ParseUtils(self.dir, self.verbose)
        # Set default values for new files
        with open(os.path.join(self.dir,self.filename),'r') as handle:
            handle.seek(0,2)
            self.len=handle.tell()
        self.after=[0]*(sectorlen-(self.len-1)%sectorlen-1)
        self.conflicting=True
        # Parse inf files
        inf_filename=os.path.join(self.dir,'.'+self.filename+'.inf')
        if os.path.isfile(inf_filename):
            with open(inf_filename,'r') as f:
                for line in f.readlines():
                    line=line.rstrip('\n').lstrip()
                    i=0
                    for arg in line.split(' '):
                        i+=1
                        try:
                            (parm, value)=arg.split(':')
                            parm=parm.strip()
                            value=value.strip()
                            parm=parm.lstrip(', ')
                            value=value.rstrip(', ')

                            if parm=='L': self.load_address=parse.hex2int(value)
                            if parm=='E': self.exec_address=parse.hex2int(value)
                            if parm=='F': self.loc=(value.strip()=='L')
                        except ValueError:
                            if i>1 and self.verbose:
                                print(
                                  "Warning: Unrecognised argument",
                                  "'{}' in {}".format(
                                    arg,
                                    '.'+self.filename+'.inf'
                                  )
                                )
                            # if i==1, first arg is allowed to not contain
                            # a colon, since it's expected to be the filename

        if os.path.isfile(inf_filename+'2'):
            def Start(value): self.start_sector=parse.hex2int(value)
            def Len(value): self.len=parse.str2int(value)
            def Index(value): self.catnum=parse.str2int(value)
            def After(value):
                self.after=[]
                while len(value)>=2:
                    self.after.append(parse.hex2int(value[0:2]))
                    value=value[2:]
                if len(value)==1:
                    if self.verbose:
                        print('Warning: After for {} has odd length;'.format(
                          self.filename
                        ), 'wiping last byte'
                        )
                    self.after.append(0)
            parse.file(
              {
              'Start sector':Start, 'Length':Len,
              'Catalogue index':Index, 'After':After
              }, '.'+self.filename+'.inf2'
            )
            self.conflicting=False # Reset flag

    def fit_file(self):
        with open(os.path.join(self.dir, self.filename),'r') as handle:
            handle.seek(0,2)
            length=handle.tell()

        orig_last_sector=self.start_sector+(self.len-1)//sectorlen
        diff_len=False
        if length!=self.len:
            if self.verbose:
                print('Info: File {} length has changed;'.format(
                  self.filename
                ),
                  'is {} bytes was {} bytes'.format(
                     length, self.len
                  )
                )
            self.len=length
            diff_len=True
        last_sector=self.start_sector+(self.len-1)//sectorlen

        if not self.conflicting:
            if last_sector > orig_last_sector:
                # Check sectors for conflicts
                for s in range(orig_last_sector+1,last_sector):
                    if self.get_sector(s) == None:
                        self.conflicting=True
                        break
                if not self.conflicting:
                    last_sector_data=self.get_sector(last_sector)
                    if last_sector_data != None:
                        # File fits; calculate after based on existing data
                        self.after=last_sector_data[(self.len-1)%sectorlen+1:]
                    else:
                        self.conflicting=True
                if self.conflicting:
                    # Mark previously full sectors as empty
                    for s in range(self.start_sector, orig_last_sector):
                        self.set_sector(s,[0]*256)
                    # Store self.after in old location
                    self.set_sector(
                      orig_last_sector,
                      [0]*(sectorlen-len(self.after))+self.after
                    )
                    if self.verbose>=2:
                        print('Info: File {} has grown beyond allotted'.format(
                          self.filename
                        ), 'space; will be moved')
                else:
                    # Claim expanded sectors as used
                    for s in range(orig_last_sector+1, last_sector+1):
                        self.set_sector(s, None)
                    if self.verbose>=2:
                        print('Info: File {} has grown to take {} extra'.format(
                          self.filename, last_sector-orig_last_sector
                        ), 'disc sectors, but it fits')
            elif last_sector < orig_last_sector:
                for s in range(last_sector+1,orig_last_sector):
                    self.set_sector(s,[0]*sectorlen)
                self.set_sector(
                  orig_last_sector,
                  [0]*(sectorlen-len(self.after))+self.after
                )
                if self.verbose>=2:
                    print('Info: File {} has shrunk, freeing up {}'.format(
                      self.filename, orig_last_sector, last_sector
                    ), 'sectors')
                self.after=[0]*(sectorlen-(self.len-1)%sectorlen-1)
            else:
                # Still ends in same sector
                last_sector_len=(self.len-1)%sectorlen+1+len(self.after)
                if last_sector_len != sectorlen:
                    # File len has changed; self.after needs tweaking
                    if self.verbose and not diff_len:
                        print("Warning: 'Bytes after' record corrupted",
                          "for {}".format(self.filename)
                        )
                    elif self.verbose>=2:
                        print('Info: File {} length changed, but still'.format(
                          self.filename
                        ), 'fits in the same allocated sectors')

                if last_sector_len>sectorlen:
                    self.after=self.after[last_sector_len-sectorlen:]
                else:
                    self.after=[0]*(sectorlen-last_sector_len)+self.after

    def read(self):
        with open(os.path.join(self.dir,self.filename),'r') as handle:
            return handle.read()

    def read_after(self):
        return list(self.after) # Modifyable copy of self.after

    def get_cat_data(self):
        '''
        Get the 8 bytes of data that go into sector 0 for every file on a disc
        '''
        block=[' ']*7
        dirflag=ord(self.dir[0])
        if self.loc:
            dirflag=dirflag | 0x80
        block.append(dirflag)
        return block

    def get_attrib_data(self):
        '''
        Get the 8 bytes of data that go into sector 1 for every file on a disc
        '''
        block=[
          (self.load_address & 0x00ff00) >> 8,
          self.load_address & 0x0000ff
        ]
        block.append((self.exec_address & 0x00ff00) >> 8)
        block.append(self.exec_address & 0x0000ff)
        block.append((self.len & 0x00ff00) >> 8)
        block.append(self.len & 0x0000ff)
        block.append(
          ((self.exec_address & 0x030000) >> 10) + # 0b11000000
          ((self.len & 0x030000) >> 12) +  # 0b001100000
          ((self.load_address & 0x030000) >> 14) + # 0b00001100
          ((self.start_sector & 0x0300) >> 8) # 0b00000011
        )
        block.append(self.start_sector & 0x0000ff)
        return block

    def is_conflicting(self):
        return self.conflicting

    def move(self, new_start_sector):
        self.start_sector=new_start_sector
        lastsector=new_start_sector+self.len//sectorlen
        try:
            for s in range(new_start_sector, lastsector):
                self.get_sector(s)[0]
            self.after=self.get_sector(lastsector)[(self.len-1)%sectorlen+1:]
        except TypeError:
            raise RuntimeError('Trying to move to occupied space!')

class TestDirFile(unittest.TestCase):
    def setUp(self):
        def get_sector(sector): return [0]*sectorlen
        def set_sector(sector,data): pass
        self.f=DirFile(
          os.path.join('test_data','DirTest1'),
          '$.FILE1',
          get_sector,set_sector,
          1
        )
        self.get_s=get_sector
        self.set_s=set_sector
        def error_sector(*args): self.assertTrue(False,'error_sector({}) called'.format(','.join([str(a) for a in args])))
        self.error_sector=error_sector

    def make_dirfile(self, filename, get_s, set_s, verbose):
        return DirFile(
          os.path.join('test_data','DirFileTest'),
          filename,
          get_s,
          set_s,
          verbose
        )

    def test_filename(self):
        self.assertEqual(self.f.filename, '$.FILE1')

    def test_load_address(self):
        self.assertEqual(self.f.load_address, 0xFF1900)
        newfile=self.make_dirfile('NEWFILE', self.get_s, self.set_s, 0)
        self.assertEqual(newfile.load_address,0x1900)

    def test_exec_address(self):
        self.assertEqual(self.f.exec_address, 0xFF8023)
        newfile=self.make_dirfile('NEWFILE', self.get_s, self.set_s, 0)
        self.assertEqual(newfile.exec_address,0x1900)

    def test_start_sector(self):
        self.assertEqual(self.f.start_sector, 0x003)
        newfile=self.make_dirfile('NEWFILE', self.get_s, self.set_s, 0)
        self.assertEqual(newfile.start_sector,2)

    def test_len(self):
        self.assertEqual(self.f.len, 270)

    def test_catnum(self):
        self.assertEqual(self.f.catnum, 0)
        newfile=self.make_dirfile('NEWFILE', self.get_s, self.set_s, 0)
        self.assertEqual(newfile.catnum,None)
        growaligned=self.make_dirfile('GROWALIGNED', self.get_s, self.set_s, 0)
        self.assertEqual(growaligned.catnum, 2)

    def test_read(self):
        self.assertEqual(len(self.f.read()), self.f.len)
        newfile=self.make_dirfile('NEWFILE', self.get_s, self.set_s, 0)
        self.assertEqual(len(newfile.read()), newfile.len)

    def test_read_after(self):
        self.assertEqual(len(self.f.read_after()),256-(self.f.len%256))
        # Test corrupted bytes after last sector entry
        oddafter=self.make_dirfile('ODDAFTER', self.error_sector, self.error_sector, 0)
        self.assertEqual(
          (len(oddafter.read_after())+oddafter.len+1)%sectorlen, 0
        )
        self.assertEqual(oddafter.read_after()[0],0xff)
        self.assertEqual(oddafter.read_after()[-2],0xff)
        self.assertEqual(oddafter.read_after()[-1],0)

    def test_fit_file(self):
        def get_s(s):
            l_got_s.append(s)
            return [0]*sectorlen

        def set_s(s,v):
            l_set_s.append(s)

        # Test grown file within sector
        grown=self.make_dirfile(
          'GROWING',
          self.error_sector, self.error_sector, 0
        )
        grown.fit_file()
        self.assertEqual(len(grown.read_after())+grown.len, sectorlen)
        self.assertEqual(grown.read_after()[0],0x88)
        self.assertEqual(grown.read_after()[-1],0x88)
        # Test shrunken file within sector
        shrunk=self.make_dirfile(
          'SHRINKING',
          self.error_sector, self.error_sector, 0
        )
        shrunk.fit_file()
        self.assertEqual(len(shrunk.read_after())%sectorlen+shrunk.len, sectorlen)
        self.assertEqual(shrunk.read_after()[0],0x00)
        self.assertEqual(shrunk.read_after()[-1],0x99)
        # Test file grown to multiple new sectors
        l_got_s=[]
        l_set_s=[]
        growmulti=self.make_dirfile('GROWMULTIPLE', get_s, set_s, 0)
        growmulti.fit_file()
        self.assertEqual(l_got_s, [4, 5])
        self.assertEqual(l_set_s, [4, 5])
        # Test file shrunk from multiple sectors
        l_set_s=[]
        shrinkmulti=self.make_dirfile(
          'SHRINKMULTIPLE'
          self.error_sector, set_s, 0
        )
        shrinkmulti.fit_file()
        self.assertEqual(l_set_s, [4, 5])
        # Test file was aligned with sectorlen, has grown
        l_got_s=[]
        l_set_s=[]
        gfromalign=self.make_dirfile('GFROMALIGNED', get_s , set_s, 0)
        gfromalign.fit_file()
        self.assertEqual(l_got_s,[11,12])
        self.assertEqual(l_set_s, [11,12])
        self.assertEqual(len(gfromalign.read_after()),sectorlen-8)
        # Test file was aligned with sectorlen, has shrunk
        l_set_s=[]
        sfromalign=self.make_dirfile(
          'SFROMALIGNED',
          self.error_sector, set_s, 0
        )
        sfromalign.fit_file()
        self.assertEqual(l_set_s, [4, 5])
        # Test file was not aligned, has grown to be aligned
        l_got_s=[]
        l_set_s=[]
        growalign=self.make_dirfile('GROWALIGNED', get_s, set_s, 0)
        growalign.fit_file()
        self.assertEqual(l_got_s, [4,5])
        self.assertEqual(l_set_s, [4,5])
        self.assertEqual(len(growalign.read_after()),0)
        # Test file was not aligned, has shrunk to be aligned
        l_set_s=[]
        shrinkalign=self.make_dirfile(
          'SHRINKALIGNED',
          self.error_sector, set_s, 0
        )
        shrinkalign.fit_file()
        self.assertEqual(l_set_s,[4,5])
        # Test file has grown into existing file - conflicting!
        def get_conflict(s):
            l_got_s.append(s)
            if s==5:
                return None
            else:
                return [0]*sectorlen

        l_got_s=[]
        l_set_s=[]
        growmulti=self.make_dirfile('GROWMULTIPLE', get_conflict, set_s, 0)
        growmulti.fit_file()
        self.assertEqual(l_got_s,[4,5])
        self.assertEqual(l_set_s,[3])

class DirDisc(DfsDisc):
    def __init__(self, directory, verbose):
        super(DirDisc, self).__init__()
        self.dir=directory
        self.verbose=verbose
        self.parse_dir()

    def parse_dir(self):
        parse=ParseUtils(self.dir,self.verbose)
        with open(os.path.join(self.dir, '..THIS_DISK.inf'),'r') as f:
            for line in f.readlines():
                if line.startswith('*OPT4,'):
                    self.boot_options=int(line[len('*OPT4,'):])
                else:
                    def T(value): self.title=value
                    def S(value): self.serial_no=parse.str2int(value)
                    parse.line(
                      line, {'T': T, 'S': S},
                      '..THIS_DISC.inf'
                    )


        def Sec(value): self.sectors=parse.hex2int(value)
        def Size(value): self.ssd_size=parse.str2int(value)
        def Noop(value): pass
        parse.file(
          {'Sectors':Sec, 'SSD file size':Size, 'Catalogue len':Noop},
          '..THIS_DISK.inf2'
        )

        # Parse the non-hidden files
        def get_sector(s): return self.read_unused_sector(s)
        def set_sector(s,v): self.set_unused_sector(s, v)

        cat=[]
        for filename in os.listdir(self.dir):
            if len(filename)!=0:
                if filename[0] != '.':
                    f=DirFile(
                      self.dir, filename, get_sector, set_sector, self.verbose
                    )
                    cat.append(f)

        # Identify unused catnums, and duplicate ones
        free_nums=[]
        for catnum in range(len(self.cat)):
            f=[dirfil for dirfil in self.cat if dirfil.catnum==catnum]
            if len(f)>1:
                for fil in f[1:]:
                    if self.verbose:
                        print('Info: File {} shares its catnum with {}'.format(
                          fil.filename, f[0].filename
                        ),'(catnum={}); renumbering it'.format(
                          fil.catnum
                        ))
                    fil.catnum=None
            elif len(f)==0:
                free_nums.append(catnum)
                if self.verbose>=2:
                    print('Info: Allocating catnum {} to a file'.format(catnum))
            # else len(f)==1

        # Assign unused catnums to unnumbered files
        for f in [dirfil for dirfil in self.cat if dirfil.catnum==None]:
            f.catnum=free_nums.pop(0)

        assert len(free_nums)==0

        self.cat=sorted(cat, key=lambda fil:fil.catnum)

        # Read ..Empty.inf
        self.sector_data = dict()
        self.unused_cat = [None, None]

        def ParseSector(sectornum, value):
            message='Warning: Unused bytes for sector {:03x}'.format(
              sectornum
            )
            return parse.text2bin(value, message)

        def SaveSector(sectornum, data):
            if self.verbose:
                message='Warning: Unused bytes for sector {:03x}'.format(
                  sectornum
                )
            if len(data) > sectorlen:
                if self.verbose:
                    print(message, 'too long; truncating')
                data=data[0:sectorlen]
            elif len(data) < sectorlen:
                if self.verbose:
                    print(message, 'too short; padding with zeroes')
                data=data+[0]*(sectorlen-len(self.sector_data[sectornum]))
            self.sector_data[sectornum]=data


        def Sector0(value): self.unused_cat[0]=ParseSector(0,value)
        def Sector1(value): self.unused_cat[1]=ParseSector(1,value)
        def Additional(value): self.additional=parse.text2bin(
          value, 'Warning: After disc image'
        )

        with open(os.path.join(self.dir, '..Empty.inf'),'r') as f:
            for line in f.readlines():
                if line.startswith('Sector '):
                    (parm, value)=line.split(':')
                    sector=int(parm[len('Sector '):])
                    SaveSector(sector,ParseSector(sector, value.strip()))
                else:
                    parse.line(
                      line,
                      {
                        'After sector 000': Sector0,
                        'After sector 001': Sector1,
                        'After disc image': Additional
                      }, '..Empty.inf'
                    )

        # Record used sectors and check for conflicts
        for fil in self.cat:
            fil.fit_file()

        # Iterate over conflicting files, biggest first
        for fil in sorted(
          [f for f in self.cat if f.is_conflicting()], key=lambda f:f.len,
          reverse=True
        ):
            size=-(-fil.len//sectorlen)
            moved=False
            for s in range(self.sectors):
                space=True
                for se in range(s, s+size):
                    if self.read_unused_sector(se) == None:
                        # Sector is in use
                        space=False
                        break
                if space:
                    fil.move(s)
                    moved=True
                    break
            if not moved:
                pass # TODO

    def read(self, start_sector, length):
        d=[]
        for s in range(start_sector, start_sector-(-length//sectorlen)):
            d+=self.read_sector(s)
        return d[:length]

    def list_unused_sectors(self):
        return self.sector_data.keys()

    def read_sector(self, sector):
        if sector<=1:
            title='{:12s}'.format(self.title)
            if sector==0:
                sectordata=[ord(c) for c in title[0:8]]
                for f in self.cat:
                    sectordata+=f.get_cat_data()
                sectordata+=self.read_unused_catalogue()[0]
            elif sector==1:
                sectordata=[ord(c) for c in title[9:]] # Bytes 0-3
                sectordata+=self.serial_no # Byte 4
                sectordata+=len(self.cat)<<3 # Byte 5
                sectordata+=(self.sectors >> 8) & 0x07 + (
                  self.boot_options << 4
                ) # Byte 6
                sectordata+=self.sectors & 0xff # Byte 7
                sectordata+=self.read_unused_catalogue()[1]
            else:
                raise RuntimeError('Negative sector asked for!')
        else:
            sectordata=self.read_unused_sector(sector)
            if sectordata==None:
                # Take the closest sector start to identify which file we're in
                f=[fil for fil in self.cat if fil.start_sector<sector]
                f=sorted(f,key=lambda fil:fil.start_sector)[-1]
                # Read the data and split it
                ss=(sector-f.start_sector)*sectorlen
                sectordata=(f.read()+f.read_after())[ss:ss+sectorlen]
        assert len(sectordata) == sectorlen
        return sectordata

    def read_unused_sector(self, sector):
        if sector in self.sector_data.keys():
            return self.sector_data[sector]
        else:
            return None

    def set_unused_sector(self, sector, data):
        if data == None:
            # Sector is now used, contrary to the name of this function
            try:
                del self.sector_data[sector]
            except KeyError:
                pass # Sector already used
        self.sector_data[sector]=data

    def read_unused_catalogue(self):
        return self.unused_cat

class TestDirDisc(unittest.TestCase):
    def setUp(self):
        self.f=DirDisc(os.path.join('test_data','DirTest1'),1)

    def test_boot_opts(self):
        self.assertEqual(self.f.boot_options, 3)

    def test_title(self):
        self.assertEqual(self.f.title, 'DIRTEST1')

    def test_serialno(self):
        self.assertEqual(self.f.serial_no, 255)

    def test_sectors(self):
        self.assertEqual(self.f.sectors, 5)

    def test_ssd_size(self):
        self.assertEqual(self.f.ssd_size, 1280)

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
