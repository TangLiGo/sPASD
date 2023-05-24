from random import randint
from Cryptodome.Cipher import AES
from bisect import bisect_left

from phe import paillier
import os
from PosOram import PosOramPort, PosPointer,DetwoOramServer
public_key, private_key = paillier.generate_paillier_keypair()
from oram_tree import BlockCipher, BlockPlaintext, Bucket, OramTree
from math import log
import math
public_key, private_key = paillier.generate_paillier_keypair()
sample_ciphertext=public_key.encrypt(3.14159)
bits_per_aes=256
bits_per_byte=8
dummy_symbol=b'\xff'
def check_range(value,range):
    if value>range:
        raise Exception("value exceeds the range",value,range)

class DataOramClient:
    key_size = 256

    def __init__(self, N, M, branching=8, data_block_bits=256):
        self.dataORAM_mainarea_size=N
        self.dataORAM_holdingarea_size=M

        self.data_block_bits=data_block_bits
        self.block_byte_size=math.ceil(self.data_block_bits/bits_per_byte)
        self.block_dummy_symbol = b'\xff'
        self.position_map=PosOramPort(dataORAM_mainarea_size=N, dataORAM_holdingarea_size=M,branching=branching,data_block_bits=data_block_bits)
        self.Ptr=self.position_map.Ptr
        self.nptr=self.Ptr.nptr
        self.write_pointer = 0
        self.key = str.encode('1' * (self.key_size // 8))
        if self.position_map.posORAM_mainarea_size==0:
            raise Exception("numnodes=0",N,M)
       # print("pos node bytes:",self.position_map.pos_node_bytes)
        dummy_blocks=self.generate_initialize_block()
        self.server=DetwoOramServer(dummy_blocks)
       # self.initialize_position_map()
        self.start_access_data_time=self.server.count
        self.start_access_pos_time = self.position_map.pos_client.server.count
      #  print(self.start_access_data_time,self.start_access_pos_time, self.pos_byte)


    def get_server_access_info(self):
        data_access_time=self.server.count-self.start_access_data_time
        pos_access_time=self.position_map.pos_client.server.count-self.start_access_pos_time

        return data_access_time,self.block_byte_size,pos_access_time,self.position_map.pos_node_bytes
    def diff(self, new_str, old_str):
        idx = 0
        # print(new_str, old_str)
      #  print("new_str, old_str",new_str, old_str)
        for i in range(self.block_byte_size):  #
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
        if idx == self.block_byte_size * bits_per_byte:
            return 0, self.get_bit(new_str, 0)
        # print("diff info",bin(old_str[0]),bin(new_str[0]),idx)
        return idx, self.get_bit(new_str, idx)

    def get_bit(self, data, i):
        byte_pos = i // bits_per_byte
        # print(len(data),byte_pos)
        # raise Exception("byte_pos",i,byte_pos,data)说明数据长度不一致
        byte_data = data[byte_pos]
        bit_pos = i % bits_per_byte
        bit_value = byte_data >> (bits_per_byte - bit_pos - 1) & 1
        return bit_value

    def read(self,block_id):

        block_data=self.decrypt_block(self.server.read(block_id))
        ptr=self.position_map.read(block_id)
        holding_pos, off_set, bit_value = self.Ptr.get(ptr)
      #  print("main area:{}; holding area:{}; self.nptr:{}, posmap.nptr:{}".format(block_id, holding_pos,self.nptr,self.position_map.nptr))
        if ptr >= self.nptr or self.get_bit(block_data,off_set)==bit_value:#block 还未被写入或者该数据为最新数据
            return block_data

       # if len(block_data)<=off_set//bits_per_byte: self.decrypt_block(self.server.read(holding_pos+self.N))
      #  print("main area:{}; holding area:{}".format(block_data, self.decrypt_block(self.server.read(holding_pos+self.N))))
        return self.decrypt_block(self.server.read(holding_pos+self.dataORAM_mainarea_size))
    def write(self, block_id, block_data):
        #   print("self.write_pointer", self.write_pointer)
        check_range(block_id, self.dataORAM_mainarea_size)
        # Refresh N/M main area blocks per-write
        start = int(
            self.write_pointer * self.dataORAM_mainarea_size / self.dataORAM_holdingarea_size) % self.dataORAM_mainarea_size
        end = int((
                              self.write_pointer + 1) * self.dataORAM_mainarea_size / self.dataORAM_holdingarea_size) % self.dataORAM_mainarea_size
        # print("start",start,end)
        if end >= start:
            refresh_range = list(range(start, end))
        else:
            refresh_range = list(range(start, self.dataORAM_mainarea_size)) + list(range(end))
        # #print("refresh_range",refresh_range)
        #   print("enter write data:refreseh:{}".format(refresh_range))
        for refresh_id in refresh_range:
            self.server.write(refresh_id, self.encrypt_block(self.read(refresh_id)))

        # filled_block_data=self.fill_block(block_data)
        # Write to Holding area
       # newest_data, mainarea_data= self.read(block_id)
       # self.server.write(self.write_pointer + self.dataORAM_mainarea_size, block_data)
        self.server.write(self.write_pointer + self.dataORAM_mainarea_size, self.encrypt_block(block_data))

       # off_set, bit_value = self.diff(block_data, mainarea_data)
        #不能是self.diff(block_data, self.server.read(block_id)),因为block_id 最新的数据可能还在holding area中，这样的话，之后读取会导致判断失误，main area中的数据被判断为最新的
      #  off_set, bit_value = self.diff(block_data, (self.read(block_id)))
        off_set, bit_value = self.diff(block_data, self.decrypt_block(self.server.read(block_id)))
        ptr = self.Ptr.create(self.write_pointer, off_set, bit_value)
        self.position_map.write(block_id, ptr)
        self.write_pointer = (self.write_pointer + 1) % self.dataORAM_holdingarea_size

        return


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
        blocks = [self.generate_dummy_block_cipher() for i in range(self.dataORAM_holdingarea_size + self.dataORAM_mainarea_size)]

        return blocks


    def generate_dummy_block_cipher(self):
        block_ciphertext=self.block_dummy_symbol * self.block_byte_size
        block_cipher = self.encrypt_block( block_ciphertext)
        return block_cipher





    def initialize_position_map(self):
        for i in range(self.dataORAM_mainarea_size):
            self.write(i, os.urandom(self.block_byte_size))

        return

