from random import randint
from Cryptodome.Cipher import AES
from bisect import bisect_left
from oram_tree import BlockCipher, BlockPlaintext, Bucket, OramTree
from math import log
import math
bits_per_aes=256
bits_per_byte=8
dummy_symbol=b'\xff'
def check_range(value,range):
    if value>range:
        raise Exception("value exceeds the range",value,range)
class DetwoOramServer:

    def __init__(self, oram_blocks):
        self.oram_blocks = oram_blocks
        self.size=len(oram_blocks)
        self.count = 0
        # init with random blocks
        # check buckets number

    def read(self, position):
        check_range(position,self.size)
        self.count += 1
        return self.oram_blocks[position]

    def write(self, position, block):
        check_range(position, self.size)
        self.count+= 1
        self.oram_blocks[position]=block

        return self.oram_blocks[position]

class PosPointer:
    def __init__(self,holdingarea_bits,diffpos_bits):
        self.holdingarea_bits=holdingarea_bits
        self.diffpos_bits=diffpos_bits
        self.ptr_bits= self.holdingarea_bits+self.diffpos_bits+1
        self.ptr_bytes=math.ceil(self.ptr_bits/bits_per_byte)
        self.mask = 2 ** self.diffpos_bits - 1
        self.nptr=dummy_symbol*self.ptr_bytes

    def create(self,holding_pos,off_set,bit_value):
       # print(self.holdsize,self.blocksize)
        check_range(holding_pos,2**self.holdingarea_bits)
        check_range(off_set, 2**self.diffpos_bits)
        data=(holding_pos<<self.diffpos_bits|off_set)<<1|bit_value
       # data=(holding_pos).to_bytes(self.holdingarea_bits,byteorder='little')+(off_set).to_bytes(self.diffpos_bits,byteorder='little')+bit_value
        data_byte=data.to_bytes(self.ptr_bytes,byteorder='little')
        return data_byte
    def get(self,data_byte):
        data=int.from_bytes(data_byte,byteorder='little')
        # holding_pos=int.from_bytes(data[:self.holdingarea_bits], byteorder='little')
        # off_set=int.from_bytes(data[self.holdingarea_bits:self.holdingarea_bits+self.diffpos_bits], byteorder='little')
        return data>>(self.diffpos_bits+1), (data>>1)&self.mask,data&1
class TrieNode:
    def __init__(self,branching,Ptr):
        self.branching=branching
        self.Ptr=Ptr
        self.ptr_bytes=self.Ptr.ptr_bytes
      #  self.dummy_byte=node_byte-branching*ptr_byte
        self.node_bytes = math.ceil(self.ptr_bytes * self.branching / (bits_per_aes / bits_per_byte))* math.ceil(bits_per_aes / bits_per_byte)
        self.data=dummy_symbol*self.node_bytes
        self.index=0
    def get(self,idx):
        return self.data[idx * self.ptr_bytes:(idx + 1) * self.ptr_bytes]

        # return self.data[self.dummy_byte+idx*self.ptr_byte:self.dummy_byte+(idx+1)*self.ptr_byte]

    def set(self,idx,ptr):
       # print(type(self.data),type(ptr))
        self.data=self.data[:idx*self.ptr_bytes]+ptr+self.data[(idx+1)*self.ptr_bytes:]
       # self.data[idx * self.ptr_bytes:(idx + 1) * self.ptr_bytes]=ptr

class TrieNodePM:
    def __init__(self,numnodes,branching,Ptr):#max_value is M
        self.numnodes=numnodes
        self.branching = branching
        self.Ptr=Ptr
        self.ptr_byte=self.Ptr.ptr_bytes
        self.nptr=self.Ptr.nptr
        self.height=self.heighthelp()

        self.minidx=1
        self.nullind=0
        self.writecache=[TrieNode(self.branching,self.Ptr) for i in range(self.height+1)]#为了简单 让block的大小与node的大小一致
        self.readcache=[TrieNode(self.branching,self.Ptr) for i in range(self.height+1)]

        # for i in range(self.branching):
        #     self.writecache[0].set(i,self.nptr)
        # for i in range(self.height+1):
        #     self.writecache[0].index=self.nullind
        #     self.readcache[0].index = self.nullind
        self.rwsplit=1#the first index where readcache diverges from writecach

        self.maxinternal=self.numnodes+self.minidx-1#max index value of the internal tree,posoram 中的index在tree中对应index+1
        self.maxidx=self.childof(self.maxinternal,self.branching-1)#max index value of the leaf nodes


    def heighthelp(self,ht=0,sofar=0,lastrow=1):
        if sofar>self.numnodes:
            return ht
        else:
            return self.heighthelp(ht+1,sofar+lastrow*self.branching,lastrow*self.branching)
    def childof(self,index,which):
        return self.branching*index+which+1
    def parentof(self,index):
        return int((index-1)/self.branching)
    def which_child(self,index):
        return (index-1)%self.branching
    def nodeind(self,idx):
        #convert node index to storage index
        return idx-self.minidx

    def path_indices(self,index,path):
        pbegin=len(path)-1
        path[pbegin]=self.parentof(index)
        while (path[pbegin]>=self.minidx):
            path[pbegin-1]=self.parentof(path[pbegin])
            pbegin-=1
        return pbegin
    def check_range(self,value,maximum):
        if value > maximum:
            raise Exception("value exceeds the range")
     #returns the length of the matching paths between the given path
     # and the given cache
    def matchlen(self,path,pbegin,sofar,cache):# pbegin is the offset to add to path indices;and sofar is the index (in cache) of the first possible mismatch
        self.check_range(len(path),len(cache)+pbegin)

        while (pbegin+sofar)<len(path) and cache[sofar].index==path[pbegin+sofar]:
            sofar+=1

        return sofar


    def write(self,index,pos,posoram):
        index+=self.minidx
        ht=self.fetch_write(index,posoram)#不一定存储在最下面那层的节点中，在path中的其中一个里？？？？
      #  print("before write")
      #  self.print_cachedata(self.writecache)
        self.writecache[ht].set(self.which_child(index),pos)

        for i in range(len(self.writecache)-1,0,-1):
            curind=self.writecache[i].index
            #!!!!!!!!!!!!!!!!dummy write
            if curind!=self.nullind:
                pos = posoram.write(self.nodeind(curind), self.writecache[i].data, self)
                self.writecache[i - 1].set(self.which_child(curind), pos)
            else:
                posoram.dummy_write(self)
        self.rwsplit=1
        self.readcache[self.rwsplit].index=self.nullind
     #   print("after write")
     #   self.print_cachedata(self.writecache)

    def fetch_read(self,index,posoram):
        path=[0 for i in range(self.height+1)]
        pbegin=self.path_indices(index,path)
        fetched=self.matchlen(path,pbegin,1,self.writecache)
      #  print("fetch read index:{}, begin:{}, fetched:{},path indices:{}".format(index ,
      #                                                                            pbegin, fetched, path))
        if (pbegin+fetched==len(path)):
            return self.writecache[fetched-1].get(self.which_child(index))

        if self.rwsplit==fetched:
            fetched=self.matchlen(path,pbegin,self.rwsplit,self.readcache)
        else:
            self.rwsplit=fetched
        if fetched>self.rwsplit:
            if pbegin+fetched==len(path):
                return self.readcache[fetched-1].get(self.which_child(index))
            else:
                find=path[pbegin + fetched]
                pos = self.readcache[fetched - 1].get(self.which_child(find))
        else:
            find = path[pbegin + fetched]
            pos = self.writecache[fetched - 1].get(self.which_child(find))
        while (pos!=self.nptr):
            self.readcache[fetched].data=(posoram.read(self.nodeind(find), pos ))
            self.readcache[fetched].index = find
            fetched+=1
            if (pbegin + fetched == len(path)):
            # found it - clear read cache below this spot and  return
                if (fetched < len(self.readcache)): self.readcache[fetched].index = self.nullind
                return self.readcache[fetched - 1].get(self.which_child(index))
            find = path[pbegin + fetched]
            pos = self.readcache[fetched - 1].get(self.which_child(find))
        self.readcache[fetched].index=self.nullind
        return pos

    def print_cachedata(self,cache):

        for i in range(len(cache)):
            out=[]
            for j in range(self.branching):
                out.append(cache[i].get(j))
            print("index:{}, ptrs:{}".format(cache[i].index,out),end="")
        print("")

    def fetch_write(self,index,posoram):
        path=[0 for i in range(self.height+1)]
        pbegin=self.path_indices(index,path)
        fetched=self.matchlen( path, pbegin, 1, self.writecache)
      #  print("fetch write index:{}, begin:{}, fetched:{},path indices:{}".format(index,pbegin,fetched,path))

        if pbegin+fetched<len(path):
            while True:
                find = path[pbegin + fetched]
                pos = self.writecache[fetched - 1].get(self.which_child(find))
                if pos==self.nptr:
                    for i in range(self.branching):
                        self.writecache[fetched].set(i,self.nptr)
                else:
                    self.writecache[fetched].data=(posoram.read(self.nodeind(find), pos))
                # if pos != self.nptr:
                #     self.writecache[fetched].write_node_data(posoram.read(self.nodeind(find), pos))
                self.writecache[fetched].index = find
                fetched += 1
                if pbegin+fetched>=len(path):
                    break
            if fetched<len(self.writecache):
                self.writecache[fetched].index = self.nullind

        return fetched - 1

    def read(self,index,posoram):
        index+=self.minidx
        pos = self.fetch_read(index,posoram)
       # print("read cache")
       # self.print_cachedata(self.writecache)
        return pos

class PosOramPort:
    key_size = 256
    def __init__(self, dataORAM_mainarea_size, dataORAM_holdingarea_size, branching=8, data_block_bits=256):

        self.block_dummy_symbol = b'\xff'
     #   self.position_map = dict()  # {block_id:  position}
     #   self.write_pointer = 0

        #get information for pos oram
        self.branching = branching
        self.posORAM_mainarea_size = math.ceil((dataORAM_mainarea_size - self.branching) / (self.branching - 1))  # numnodes 没有将root node算上
        self.posORAM_treelevel=self.heighthelp()#int(log(self.posORAM_mainarea_size+1, self.branching))
        self.posORAM_holdingarea_size=self.posORAM_mainarea_size * (self.posORAM_treelevel)
       # print("d",math.ceil(log((self.branching-1)*(self.posORAM_mainarea_size+1)+1,self.branching)))
      #  print("self.posORAM_treelevel:{} cmpute h:{},Mp:{}".format(self.posORAM_treelevel,math.ceil(log((self.branching-1)*self.posORAM_mainarea_size+self.branching,self.branching)-1),self.posORAM_holdingarea_size))
        self.ptr_holdingarea_bits=math.ceil(log(max(dataORAM_holdingarea_size,self.posORAM_holdingarea_size)+1,2))#+1是为了能有nptr
       # leaf_node_min_size=math.ceil(self.ptr_holdingarea_bits+log(data_block_bits,2)+1)*branching
        leaf_node_min_size=math.ceil(math.ceil((self.ptr_holdingarea_bits+log(data_block_bits,2)+1)/bits_per_byte)*self.branching/(bits_per_aes/bits_per_byte))*bits_per_aes
        #diff 针对每一个ptr 而不是每个node
        #self.ptr_diffpos_bits = int(log(self.data_block_size, 2))
        # # diff 针对每个node
        if leaf_node_min_size<=data_block_bits:
            self.ptr_diffpos_bits = math.ceil(log(data_block_bits,2))
        else:
            last_block_size = math.ceil(math.ceil(
                (self.ptr_holdingarea_bits + log(data_block_bits, 2) + 1) / bits_per_byte) * self.branching / (
                                                       bits_per_aes / bits_per_byte)) * bits_per_aes

            #last_block_size=(self.ptr_holdingarea_bits + math.ceil(log(data_block_bits, 2)) + 1) * branching
            for i in range(self.posORAM_treelevel):
                last_block_size = math.ceil(math.ceil(
                (self.ptr_holdingarea_bits + log(last_block_size, 2) + 1) / bits_per_byte) * self.branching / (
                                                       bits_per_aes / bits_per_byte)) * bits_per_aes
            self.ptr_diffpos_bits = math.ceil(log(last_block_size, 2))
        self.Ptr = PosPointer(self.ptr_holdingarea_bits, self.ptr_diffpos_bits)  # ???

        self.pos_node_bytes=math.ceil(self.Ptr.ptr_bytes*self.branching/(bits_per_aes/bits_per_byte))*math.ceil(bits_per_aes/bits_per_byte)
       # self.pos_dummy_bytes=self.pos_node_bytes-self.Ptr.ptr_bytes*self.branching
        self.nptr=self.block_dummy_symbol*self.Ptr.ptr_bytes
        self.key = str.encode('1' * (self.key_size // 8))
        self.triepm = TrieNodePM(self.posORAM_mainarea_size, branching, self.Ptr)
        self.pos_client = PosOramClient(posORAM_mainarea_size=self.posORAM_mainarea_size,posORAM_holdingarea_size=self.posORAM_holdingarea_size, Ptr=self.Ptr,block_bytes=self.pos_node_bytes)


    def heighthelp(self,ht=0,sofar=0,lastrow=1):
        if sofar>self.posORAM_mainarea_size:
            return ht
        else:
            return self.heighthelp(ht+1,sofar+lastrow*self.branching,lastrow*self.branching)

    def write(self,index,pos):
       # print("write index:{},pos:{},Np:{}".format(index,pos,self.numnodes))
        self.triepm.write(index+self.posORAM_mainarea_size,pos,self.pos_client)
    def read(self,index):
        return self.triepm.read(index+self.posORAM_mainarea_size,self.pos_client)
class PosOramClient:
    key_size = 256

    def __init__(self,posORAM_mainarea_size,posORAM_holdingarea_size, Ptr,block_bytes):
        self.posORAM_mainarea_size=posORAM_mainarea_size
        self.posORAM_holdingarea_size=posORAM_holdingarea_size
        self.Ptr = Ptr
        self.nptr = self.Ptr.nptr
        self.block_dummy_symbol = b'\xff'
        self.write_pointer = 0
        self.block_bytes = block_bytes
        self.key = str.encode('1' * (self.key_size // 8))
        dummy_buckets = self.generate_initialize_block()
        self.server = DetwoOramServer(dummy_buckets)


    def diff(self,new_str, old_str):
        idx = 0
        #print(new_str, old_str)
        for i in range(self.block_bytes):  #
            if old_str[i] != new_str[i]:
                x = old_str[i] ^ new_str[i]
                temp = 0  # temp 的大小等于byte中不同bit的数量
              #  while (x & (2 ** bits_per_byte - 1)) != 0 and temp < bits_per_byte + 1:
                while x != 0 and temp < bits_per_byte + 1:
                    x = x >> 1
                    temp += 1
                idx += bits_per_byte - temp
                break
            idx += bits_per_byte
            # idx=0 代表完整相同,idx=3 代表第3个bit不一样
        if idx==self.block_bytes*bits_per_byte:
            return 0, self.get_bit(new_str,0)
        #print("diff info",bin(old_str[0]),bin(new_str[0]),idx)
        return idx, self.get_bit(new_str,idx)
    def get_bit(self,data,i):
        byte_pos = i // bits_per_byte
       # print(len(data),byte_pos)
           # raise Exception("byte_pos",i,byte_pos,data)说明数据长度不一致
        byte_data = data[byte_pos]
        bit_pos = i % bits_per_byte
        bit_value = byte_data >> (bits_per_byte - bit_pos - 1) & 1
        return bit_value
    def read(self,block_id, ptr):

        block_data=self.decrypt_block(self.server.read(block_id))
        # #print("block",block_data,len(block_data),off_set)
        # if off_set<len(block_data):
        #     #print("byte",self.get_byte(block_data,off_set),bit_value)
        holding_pos, off_set, bit_value = self.Ptr.get(ptr)
        # print("Read data:self.block_id:{},ptr:{},holding_pos+N:{},data_range:{}".format(block_id, ptr, holding_pos + self.N,
        #                                                                   self.N + self.M))
        #print("in func read",ptr,(holding_pos, off_set, bit_value),self.get_bit(block_data,off_set))
       # print("ptr",self.Ptr.get(ptr),ptr,self.nptr)
        if ptr >= self.nptr or self.get_bit(block_data,off_set)==bit_value:#block 还未被写入或者该数据为最新数据
            return block_data

       # if len(block_data)<=off_set//bits_per_byte: self.decrypt_block(self.server.read(holding_pos+self.N))

        return self.decrypt_block(self.server.read(holding_pos+self.posORAM_mainarea_size))

    def write(self, block_id, block_data, pos_map):
        #   print("self.write_pointer", self.write_pointer)
        check_range(block_id, self.posORAM_mainarea_size)
        # Refresh N/M main area blocks per-write
        start = int(self.write_pointer * self.posORAM_mainarea_size / self.posORAM_holdingarea_size) % self.posORAM_mainarea_size
        end = int((self.write_pointer + 1) * self.posORAM_mainarea_size / self.posORAM_holdingarea_size) % self.posORAM_mainarea_size
        # print("start",start,end)
        if end >= start:
            refresh_range = list(range(start, end))
        else:
            refresh_range = list(range(start, self.posORAM_mainarea_size)) + list(range(end))
        # #print("refresh_range",refresh_range)
        #   print("enter write data:refreseh:{}".format(refresh_range))
        for refresh_id in refresh_range:
            pos_ptr = pos_map.read(refresh_id, self)
            new_cipher = self.encrypt_block(self.read(refresh_id, pos_ptr))
            self.server.write(refresh_id, new_cipher)
        # filled_block_data=self.fill_block(block_data)
        # Write to Holding area
        self.server.write(self.write_pointer + self.posORAM_mainarea_size, self.encrypt_block(block_data))
        # compute position map
        off_set, bit_value = self.diff(block_data, self.decrypt_block(self.server.read(block_id)))
        # if off_set==self.block_byte_size*bits_per_byte: off_set=0
        # print("self.write_pointer:{},off_set:{},bit_value:{},blockbits:{}".format(self.write_pointer,off_set,bit_value,self.Ptr.blockbits))

        ptr = self.Ptr.create(self.write_pointer, off_set, bit_value)
        #      print("write data:self.block_id:{},ptr:{},data_range:{}".format(block_id, ptr, self.N + self.M))
        # print("ptr:{},ptr_dec:{}".format(ptr,self.Ptr.get(ptr)))
        #   #print("ptr data",ptr)
        self.write_pointer = (self.write_pointer + 1) % self.posORAM_holdingarea_size

        return ptr


    def encrypt_block(self, block_plaintext):
        cipher = AES.new(self.key, AES.MODE_EAX)
        nonce = cipher.nonce
        # padded_block_id = block_plaintext.block_id.to_bytes(self.block_id_size, byteorder='little')
        # data = padded_block_id + block_plaintext.data
        ciphertext = cipher.encrypt(block_plaintext)
        return BlockCipher(ciphertext, nonce)

    def decrypt_block(self, block_cipher):
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=block_cipher.nonce)
        plain_text = cipher.decrypt(block_cipher.cipher)

        return plain_text

    def generate_initialize_block(self):
        blocks = [self.generate_dummy_block_cipher() for i in range(self.posORAM_holdingarea_size+self.posORAM_mainarea_size)]

        return blocks


    def generate_dummy_block_cipher(self):
        block_ciphertext=self.block_dummy_symbol * self.block_bytes
        block_cipher = self.encrypt_block( block_ciphertext)
        return block_cipher
    def dummy_write(self, pos_map):
       # print("self.N / self.M",self.N, self.M)
        # Refresh N/M main area blocks per-write
        start = int(self.write_pointer * self.posORAM_mainarea_size / self.posORAM_holdingarea_size) % self.posORAM_mainarea_size
        end = int((self.write_pointer + 1) * self.posORAM_mainarea_size / self.posORAM_holdingarea_size) % self.posORAM_mainarea_size
        #  #print("start",start,end)
        if end >= start:
            refresh_range = list(range(start, end))
        else:
            refresh_range = list(range(start, self.posORAM_mainarea_size)) + list(range(end))
        # #print("refresh_range",refresh_range)
        #   print("enter write data:refreseh:{}".format(refresh_range))
        for refresh_id in refresh_range:
            pos_ptr = pos_map.read(refresh_id, self)
            new_cipher = self.encrypt_block(self.read(refresh_id, pos_ptr))
            self.server.write(refresh_id, new_cipher)
        # filled_block_data=self.fill_block(block_data)
        # Write to Holding area
        self.server.write(self.write_pointer + self.posORAM_mainarea_size, self.block_dummy_symbol)

        self.write_pointer = (self.write_pointer + 1) % self.posORAM_holdingarea_size

        return

