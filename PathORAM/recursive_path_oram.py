from random import randint
from Cryptodome.Cipher import AES
from bisect import bisect_left
from oram_tree import BlockCipher, BlockPlaintext, Bucket, OramTree
from math import log
import math

class RecursivePathOramServer:

    # block_size default to 2048 bytes
    # block_id_size 32 bytes
    #
    # a simple construction of a block
    # a block composed of two part = (cipher, nonce)
    # cipher = block_id + data   block_id = 256 bit = 32 bytes
    # nonce = AES nonce , used for decryption
    # A file could be stored in multiple block,  a mapping between file and block_id could be stored in client
    #
    # block dummy symbol used to pad a file to the maximum size which is (block_size - block_id_size)
    #

    def __init__(self, oram_buckets):
        self.oram_tree = []
        self.count = []
        # init with random blocks
        # check buckets number
        for buckets in oram_buckets:
            self.oram_tree.append(OramTree(buckets))
            self.count.append(0)

    def read(self, position, recursive_level):
        self.count[recursive_level] += 1
        return self.oram_tree[recursive_level].read(position)

    def write_bucket(self, position, blocks, level, recursive_level):
        self.count[recursive_level] += 1
        return self.oram_tree[recursive_level].write(position, blocks, level)



class RecursivePathOramClient:
    key_size = 256

    # block_size default to 2048 bytes
    # block_id_size 32 bytes
    #
    # a simple construction of a block
    # a block composed of two part = (cipher, nonce)
    # cipher = block_id + data   block_id = 256 bit = 32 bytes
    # nonce = AES nonce , used for decryption
    # A file could be stored in multiple block,  a mapping between file and block_id could be stored in client
    #
    # block dummy symbol used to pad a file to the maximum size which is (block_size - block_id_size)

    # Data of position block is (block_id+position)
    # assume a position compress with 2^k for simplicity
    # we do not need to hide the size of position map block, the size could be calculated.
    def __init__(self, first_level, Z=4, position_compress=8, block_size=256, block_id_size=16):
        # assume position_compress is the size of 2^k for simplicity
        if log(position_compress, 2) != int(log(position_compress, 2)):
            raise Exception("position block level should be the pow of 2")

        first_level_leaf_nodes = pow(2, first_level)  # real file blocks no more than this

        recursive_level = int(log(first_level_leaf_nodes-1, position_compress))

        self.recursive_level = recursive_level

        # calculate level for all oram
        self.levels = [first_level]
        self.blocks_size = [block_size]
        self.max_stash_size = [0 for i in range(self.recursive_level + 1)]
        previous_leaf_nodes = first_level_leaf_nodes
        for i in range(1, recursive_level + 1):
            leaf_nodes = previous_leaf_nodes / position_compress
            position_block_size = block_id_size + self.levels[-1]#last level's leaf nodes' id and corresponding node
            level = int(log(leaf_nodes, 2))
            self.levels.append(level)
            self.blocks_size.append(position_block_size)
            previous_leaf_nodes = leaf_nodes
        print("all levels:", self.levels)
        self.Z = Z
        self.block_id_size = block_id_size

        self.block_dummy_symbol = b'\xff'
        self.dummy_block_id = int.from_bytes(self.block_dummy_symbol * self.block_id_size, byteorder='little')

        self.position_compress = position_compress  # 24

        self.stash = [dict() for i in range(recursive_level + 1)]  # {block_id: block plaintext)}

        self.position_map = dict()  # {block_id:  position}

        # use AES for encryption
        self.key = str.encode('1' * (self.key_size // 8))

    def find_intersection_block(self, position, level, recursive_level, oram_server):
        intersect_block = dict()
        for block_id in self.stash[recursive_level]:
            read_blockpos=self.lookup_position_find_intersection(block_id, recursive_level + 1, oram_server)
            block_position = position if read_blockpos==None else read_blockpos
            if block_position[:level] == position[:level]:
                intersect_block[block_id] = self.stash[recursive_level][block_id]
        return intersect_block

    def lookup_position_find_intersection(self, block_id, recursive_level, oram_server):
        compressed_block_id = block_id // self.position_compress

        if recursive_level == self.recursive_level + 1:  # last level
            position = self.position_map[compressed_block_id]
        else:  # read position from recursive oram
            data = self.read_recursively(compressed_block_id, recursive_level, oram_server)

            # get position of target block from packed data
            block_size = self.blocks_size[recursive_level]
            if len(data) % block_size != 0:
                raise Exception("unexpected length of data read", "length of data", len(data), "block size", block_size)
            in_block_id=block_id%self.position_compress
            block = data[in_block_id * block_size:(in_block_id + 1) * block_size]
            if block==self.block_dummy_symbol*block_size:
                position = None
            else:
                position = block[self.block_id_size:block_size].decode()

            # found = False
            # position = ''
            # data_to_write = None
            # for i in range(0, len(data) // block_size):
            #     block = data[i * block_size:(i + 1) * block_size]
            #     read_block_id = int.from_bytes(block[:self.block_id_size], byteorder='little')
            #     if read_block_id != block_id:
            #         continue
            #     found = True
            #     position = block[self.block_id_size:block_size].decode()
            #     break
            # if not found:
            #     raise Exception("position should be found")
            # write new position
        return position

    def lookup_position(self, block_id, recursive_level, oram_server):
        compressed_block_id = block_id // self.position_compress
        leaf_nodes = pow(2, self.levels[recursive_level - 1])
        new_position = self.integer_to_position(randint(0, leaf_nodes), recursive_level - 1)
        if recursive_level == self.recursive_level + 1:  # last level
            position = self.position_map[compressed_block_id]
            self.position_map[compressed_block_id] = new_position
        else:  # read position from recursive oram
            data = self.read_recursively(compressed_block_id, recursive_level, oram_server)


            # get position of target block from packed data
            block_size = self.blocks_size[recursive_level]
            if len(data) % block_size != 0:
                raise Exception("unexpected length of data read", "length of data", len(data), "block size", block_size)
            found = False
            position = ''
         #   data_to_write = None
            in_block_id=block_id%self.position_compress
            block = data[in_block_id * block_size:(in_block_id + 1) * block_size]
            if block==self.block_dummy_symbol*block_size:
                position = new_position
            else:
                position = block[self.block_id_size:block_size].decode()
            new_position_data = block_id.to_bytes(self.block_id_size, byteorder='little') + new_position.encode()
            data_to_write = data[:in_block_id * block_size] + new_position_data + data[(in_block_id + 1) * block_size:]


            # for i in range(0, len(data) // block_size):
            #     block = data[i * block_size:(i + 1) * block_size]
            #     read_block_id = int.from_bytes(block[:self.block_id_size], byteorder='little')
            #     if read_block_id != block_id:
            #         continue
            #     found = True
            #     position = block[self.block_id_size:block_size].decode()
            #     new_position_data = block_id.to_bytes(self.block_id_size, byteorder='little') + new_position.encode()
            #     data_to_write = data[:i * block_size] + new_position_data + data[(i + 1) * block_size:]
            #     break
            # if not found:
            #
            #     raise Exception("position should be found")
            self.write_recursively(compressed_block_id, data_to_write, recursive_level, oram_server)
            # write new position
        return position

    def access(self, op, block_id, block_data, recursive_level, oram_server):
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
