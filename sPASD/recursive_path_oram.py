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
        self.count = []
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
    def create(self,holding_pos,off_set,bit_value):
       # print(self.holdsize,self.blocksize)
        check_range(holding_pos,self.holdingarea_bits)
        check_range(off_set, self.diffpos_bits)
        data=(holding_pos<<self.ptr_bits|off_set)<<1|bit_value
       # data=(holding_pos).to_bytes(self.holdingarea_bits,byteorder='little')+(off_set).to_bytes(self.diffpos_bits,byteorder='little')+bit_value
        data=data.to_bytes(self.ptr_bytes,byteorder='little')
        return data
    def get(self,data):
        holding_pos=int.from_bytes(data[:self.holdingarea_bits], byteorder='little')
        off_set=int.from_bytes(data[self.holdingarea_bits:self.holdingarea_bits+self.diffpos_bits], byteorder='little')
        return holding_pos,off_set,
class TrieNode:
    def __init__(self,branching,ptr_byte):
        self.branching=branching
        self.ptr_byte=ptr_byte
      #  self.dummy_byte=node_byte-branching*ptr_byte
        self.data=b''
        self.index=0
    def get(self,idx):
        return self.data[ idx * self.ptr_byte:(idx + 1) * self.ptr_byte]

        # return self.data[self.dummy_byte+idx*self.ptr_byte:self.dummy_byte+(idx+1)*self.ptr_byte]

    def set(self,idx,ptr):
        self.data[idx * self.ptr_byte:(idx + 1) * self.ptr_byte]=ptr

class TrieNodePM:
    def __init__(self,numnodes,branching,Ptr,ptr_byte):#max_value is M
        self.numnodes=numnodes
        self.branching = branching
        self.Ptr=Ptr
        self.ptr_byte=ptr_byte
        self.nptr=self.Ptr.nptr
        self.height=self.heighthelp()

        self.minidx=1
        self.nullind=0
        self.writecache=[TrieNode(self.branching,self.ptr_byte) for i in range(self.height+1)]#为了简单 让block的大小与node的大小一致
        self.readcache=[TrieNode(self.branching,self.ptr_byte) for i in range(self.height+1)]

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
class PosDetWoORAMClient:
    key_size = 256
    def __init__(self, dataORAM_mainarea_size, dataORAM_holdingarea_size, branching=8, data_block_bits=256):

        self.block_dummy_symbol = b'\xff'
        self.position_map = dict()  # {block_id:  position}
        self.write_pointer = 0

        #get information for pos oram
        self.branching = branching
        self.posORAM_mainarea_size = math.ceil((dataORAM_mainarea_size - self.branching) / (self.branching - 1))  # numnodes 没有将root node算上
        self.posORAM_treelevel=self.heighthelp()#int(log(self.posORAM_mainarea_size+1, self.branching))
        self.posORAM_holdingarea_size=self.posORAM_mainarea_size * self.posORAM_treelevel
        self.ptr_holdingarea_bits=int(log(max(dataORAM_holdingarea_size,self.posORAM_holdingarea_size)+1,2))#+1是为了能有nptr
        leaf_node_min_size=int(log(self.ptr_holdingarea_bits,2)+log(data_block_bits,2)+1)*branching
        #diff 针对每一个ptr 而不是每个node
        #self.ptr_diffpos_bits = int(log(self.data_block_size, 2))
        # # diff 针对每个node
        if leaf_node_min_size<=data_block_bits:
            self.ptr_diffpos_bits = int(log(data_block_bits,2))
        else:
            last_block_size=int(log(self.ptr_holdingarea_bits, 2) + log(data_block_bits, 2) + 1) * branching
            for i in range(self.posORAM_treelevel):
                last_block_size = int(log(self.ptr_holdingarea_bits+1, 2) + log(last_block_size, 2) + 1) * branching
            self.ptr_diffpos_bits = int(log(last_block_size, 2))
        self.Ptr = PosPointer(self.ptr_holdingarea_bits, self.ptr_diffpos_bits)  # ???

        self.pos_node_bytes=math.ceil(self.Ptr.ptr_bytes*self.branching/(bits_per_aes/bits_per_byte))*(bits_per_aes/bits_per_byte)
        self.pos_dummy_bytes=self.pos_node_bytes-self.Ptr.ptr_bytes*self.branching
        self.nptr=self.block_dummy_symbol*self.Ptr.ptr_bytes
        self.key = str.encode('1' * (self.key_size // 8))
        self.triepm = TrieNodePM(self.posORAM_holdingarea_size, branching, self.Ptr, self.ptr_byte)

    def heighthelp(self,ht=0,sofar=0,lastrow=1):
        if sofar>self.posORAM_mainarea_size:
            return ht
        else:
            return self.heighthelp(ht+1,sofar+lastrow*self.branching,lastrow*self.branching)


class DataDetWoOramClient:
    key_size = 256

    def __init__(self, N, M, branching=8, data_block_bits=256):
        self.dataORAM_mainarea_size=N
        self.dataORAM_holdingarea_size=M

        self.data_block_bits=data_block_bits
        self.block_dummy_symbol = b'\xff'
        self.position_map = dict()  # {block_id:  position}
        self.write_pointer = 0

        #get information for pos oram
        self.branching = branching
        self.posORAM_mainarea_size = math.ceil((self.dataORAM_mainarea_size - self.branching) / (self.branching - 1))  # numnodes 没有将root node算上
        self.posORAM_treelevel=self.heighthelp()#int(log(self.posORAM_mainarea_size+1, self.branching))
        self.posORAM_holdingarea_size=self.posORAM_mainarea_size * self.posORAM_treelevel
        self.ptr_holdingarea_bits=int(log(max(self.dataORAM_holdingarea_size,self.posORAM_holdingarea_size)+1,2))#+1是为了能有nptr
        leaf_node_min_size=int(log(self.ptr_holdingarea_bits,2)+log(self.data_block_bits,2)+1)*branching
        #diff 针对每一个ptr 而不是每个node
        #self.ptr_diffpos_bits = int(log(self.data_block_size, 2))
        # # diff 针对每个node
        if leaf_node_min_size<=self.data_block_bits:
            self.ptr_diffpos_bits = int(log(self.data_block_bits,2))
        else:
            last_block_size=int(log(self.ptr_holdingarea_bits, 2) + log(self.data_block_bits, 2) + 1) * branching
            for i in range(self.posORAM_treelevel):
                last_block_size = int(log(self.ptr_holdingarea_bits+1, 2) + log(last_block_size, 2) + 1) * branching
            self.ptr_diffpos_bits = int(log(last_block_size, 2))
        self.Ptr = PosPointer(self.ptr_holdingarea_bits, self.ptr_diffpos_bits)  # ???

        self.pos_node_bytes=math.ceil(self.Ptr.ptr_bytes*self.branching/(bits_per_aes/bits_per_byte))*(bits_per_aes/bits_per_byte)
        self.pos_dummy_bytes=self.pos_node_bytes-self.Ptr.ptr_bytes*self.branching
        self.nptr=self.block_dummy_symbol*self.Ptr.ptr_bytes
        self.key = str.encode('1' * (self.key_size // 8))

    def heighthelp(self,ht=0,sofar=0,lastrow=1):
        if sofar>self.posORAM_mainarea_size:
            return ht
        else:
            return self.heighthelp(ht+1,sofar+lastrow*self.branching,lastrow*self.branching)




    def write(self, op, block_id, block_data, recursive_level, oram_server):
        # print("recursive level",recursive_level)
        block_position = self.lookup_position(block_id, recursive_level + 1, oram_server)
        # read bucket along path block_position from server
        blocks_cipher = oram_server.read(block_position, recursive_level)
        to_append_stash = dict()
        test_data=''
        for block_cipher in blocks_cipher:
            block_plaintext = self.decrypt_block(block_cipher)
            # skip dummy block
            if block_plaintext.block_id == self.dummy_block_id:
                continue
            to_append_stash[block_plaintext.block_id] = block_plaintext
            test_data=block_plaintext.data

        # update stash
        self.stash[recursive_level].update(to_append_stash)
        # print("stash:",self.stash[recursive_level],"recusieve level",recursive_level)
        if block_id not in self.stash[recursive_level]:
            if recursive_level != 0:#
                # not first level, must exists
                data_to_read=self.block_dummy_symbol * self.blocks_size[recursive_level]*self.position_compress
                #work的前提是position nodes均已正确初始化
             #   raise Exception("position must exists in position oram",block_id,recursive_level)
            # not write before
            else:
                data_to_read = None

        else:
            block_plaintext_to_read = self.stash[recursive_level][block_id]  # read from stash a
            if recursive_level == 0:  # only remove dummy for file blocks
                data_to_read = self.remove_dummy_in_block(block_plaintext_to_read.data)
            else:
                data_to_read = block_plaintext_to_read.data
        if op == 'write':
            if recursive_level == 0:  # only padding for file block
                block_size = self.blocks_size[0]
                # pad block data to maximum block_size
                if len(block_data) > block_size:
                    raise Exception("length of block data should be less than block size", "length of block data:",
                                    len(block_data), "block size:", block_size)
                block_data = block_data + (self.blocks_size[0] - len(block_data)) * self.block_dummy_symbol

            self.stash[recursive_level][block_id] = BlockPlaintext(block_id, block_data)

        for l in reversed(range(self.levels[recursive_level] + 1)):
            intersect_block = self.find_intersection_block(block_position, l, recursive_level, oram_server)
            # select S'= min(len(intersect_block),Z) blocks to write
            select_block_num = min(len(intersect_block), self.Z)
            count = 0
            select_block_id = dict()
            for k in intersect_block:
                if count == select_block_num:
                    break
                select_block_id[k] = intersect_block[k]
                count += 1

            # remove select block from stash
            for block_id in select_block_id:
                del self.stash[recursive_level][block_id]

            select_blocks = [select_block_id[k] for k in select_block_id]

            select_blocks_cipher = []
            for select_block in select_blocks:
                block_cipher = self.encrypt_block(select_block)
                select_blocks_cipher.append(block_cipher)

            # padded S' with dummy blocks to size of Z, block id should be selected from stash
            if len(select_blocks_cipher) < self.Z:
                dummy_blocks_cipher = []
                for i in range(0, self.Z - len(select_blocks_cipher)):
                    dummy_block_cipher = self.generate_dummy_block_cipher(recursive_level)
                    dummy_blocks_cipher.append(dummy_block_cipher)
                select_blocks_cipher.extend(dummy_blocks_cipher)
            oram_server.write_bucket(block_position, select_blocks_cipher, l, recursive_level)
        return data_to_read

    def remove_dummy_in_block(self, data):
        dummy_symbol = self.block_dummy_symbol
        dummy_symbol_value = dummy_symbol[0]
        first_dummy_index = bisect_left(data, dummy_symbol_value)
        return data[:first_dummy_index]

    def read(self, block_id, oram_server):
        return self.read_recursively(block_id, 0, oram_server)

    def write(self, block_id, block_data, oram_server):
        return self.write_recursively(block_id, block_data, 0, oram_server)

    def read_recursively(self, block_id, recursive_level, oram_server):
        return self.access(op='read', block_data=None, block_id=block_id, recursive_level=recursive_level,
                           oram_server=oram_server)

    def write_recursively(self, block_id, block_data, recursive_level, oram_server):
        return self.access(op='write', block_id=block_id, block_data=block_data, recursive_level=recursive_level,
                           oram_server=oram_server)

    def encrypt_block(self, block_plaintext):
        cipher = AES.new(self.key, AES.MODE_EAX)
        nonce = cipher.nonce
        padded_block_id = block_plaintext.block_id.to_bytes(self.block_id_size, byteorder='little')
        data = padded_block_id + block_plaintext.data
        ciphertext = cipher.encrypt(data)
        return BlockCipher(ciphertext, nonce)

    def decrypt_block(self, block_cipher):
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=block_cipher.nonce)
        plain_text = cipher.decrypt(block_cipher.cipher)
        block_id = int.from_bytes(plain_text[:self.block_id_size], byteorder='little')
        data = plain_text[self.block_id_size:]
        return BlockPlaintext(block_id, data)

    def generate_initialize_block(self):
        oram_buckets = []
        ## generate data blocks '
        level = self.levels[0]
        block_size = self.blocks_size[0]
        total_bucket_number = pow(2, level + 1) - 1
        blocks = [[self.generate_dummy_block_cipher(recursive_level=0)] * self.Z for i in range(total_bucket_number)]

        buckets = []
        for i in range(len(blocks)):
            bucket = Bucket(blocks[i])
            buckets.append(bucket)

        oram_buckets.append(buckets)
        position_buckets = self.generate_initialize_position_block()
        oram_buckets.extend(position_buckets)

        return oram_buckets

    def generate_initialize_position_block(self):
        level_buckets = []
        for i in range(1, self.recursive_level + 1):
            level = self.levels[i]
            middle_buckets_blocks = [[self.generate_dummy_block_cipher(i)] * self.Z for k in
                                     range(pow(2, level + 1) - 1)]
            level = self.levels[i]
            leaf_nodes = pow(2, level)
            level_position_data = []

            previous_leaf_nodes = pow(2, self.levels[i - 1])
            for j in range(previous_leaf_nodes):
                block_id = j.to_bytes(self.block_id_size, byteorder='little')
                position = self.integer_to_position(j, i - 1).encode()
                data = block_id + position
                level_position_data.append(data)
            level_position_blocks = []
            for j in range(0, leaf_nodes):
                packed_data = b''.join(level_position_data[j * self.position_compress:(j + 1) * self.position_compress])
                packed_block = BlockPlaintext(j, packed_data)
                packed_block_cipher = self.encrypt_block(packed_block)
                level_position_blocks.append(packed_block_cipher)

            leaf_nodes_index = range(leaf_nodes - 1, leaf_nodes * 2 - 1)

            if len(leaf_nodes_index) != len(level_position_blocks):
                raise Exception("unexpected wrong", len(leaf_nodes_index))

            for j, index in enumerate(leaf_nodes_index):
                middle_buckets_blocks[index][0] = level_position_blocks[j]

            middle_buckets = []
            for j in range(pow(2, level + 1) - 1):
                middle_buckets.append(Bucket(middle_buckets_blocks[j]))
            level_buckets.append(middle_buckets)

        # for last level
        last_level = self.levels[-1]
        last_level_leaf_nodes = pow(2, last_level)
        for i in range(last_level_leaf_nodes):
            self.position_map[i] = self.integer_to_position(i, self.recursive_level)
        return level_buckets

    def generate_dummy_block_cipher(self, recursive_level):
        block_size = self.blocks_size[recursive_level]
        dummy_block = self.block_dummy_symbol * block_size
        dummy_block_id = int.from_bytes(dummy_block[:self.block_id_size], byteorder='little')
        if recursive_level == 0:
            dummy_data = dummy_block[self.block_id_size: block_size]
            block_cipher = self.encrypt_block(
                BlockPlaintext(dummy_block_id, dummy_data))
        else:
            block_cipher = self.encrypt_block(
                BlockPlaintext(dummy_block_id, dummy_block * self.position_compress)
            )
        return block_cipher

    # change loc from 0 - 2^ level - 1 to a binary position representation in a tree (e.g. '00101')
    def integer_to_position(self, loc, recursive_level):
        binary_loc = bin(loc)[2:]  # remove '0b' in binary
        position_length = self.levels[recursive_level]
        position = ('0' * position_length + binary_loc)[-position_length:]
        return position
