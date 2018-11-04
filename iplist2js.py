#!/usr/bin/env python3


from ipaddress import ip_network
import json
import sys


def ip_to_bin(s):
    parsed = ip_network(s, strict=False)
    ip_addr = parsed.network_address
    ip_bytes = ip_addr.packed

    def byte_to_bin_array(b):
        masks = (
            0b10000000, 0b01000000, 0b00100000, 0b00010000,
            0b00001000, 0b00000100, 0b00000010, 0b00000001,
        )
        return [ int(bool(b & m)) for m in masks ]
    bin_array = sum((byte_to_bin_array(x) for x in ip_bytes), [])
    return bin_array[:parsed.prefixlen]


def bin_to_ip(bin):
    def bin_array_to_octet(bin):
        ret = 0
        for sh in range(8):
            ret += bin[8 - 1 - sh] << sh
        return ret
    prefix_len = len(bin)
    ip_bin_array = bin + (32 - len(bin)) * [0]
    ip_bin_array_four = [ip_bin_array[0:8], ip_bin_array[8:16], ip_bin_array[16:24], ip_bin_array[24:32]]
    ip = '.'.join(str(bin_array_to_octet(x)) for x in ip_bin_array_four)
    return '{ip}/{prefix}'.format(ip=ip, prefix=prefix_len)


def tree_is_empty(tree):
    return tree == [None, None]


def create_tree(bins):
    def add_to_tree(tree, bin, extend=False):
        # extend 变量防止树的末端增长，即一个大的网段包住一个小的网段。正常情况是树产生分支，而不是末端增长。
        # 第一次往 root 节点（即 [None, None]）添加网段时要设置 extend 为 True
        if extend is False and tree[0] is None and tree[1] is None:
            return

        if len(bin) == 0:
            # 大网段包住小的网段，强行变成大网段。
            if extend is False:
                tree[0] = tree[1] = None
                return
            # 正常结束
            return

        bit = bin[0]
        if tree[bit] is None:
            tree[bit] = [None, None]
            extend = True
        if len(bin) > 0:
            add_to_tree(tree[bit], bin[1:], extend=extend)

    tree = [None, None]
    extend = True
    for bin in bins:
        add_to_tree(tree, bin, extend)
        extend = False
    return tree


def optimize_tree(tree):
    """合并相邻网段
              Parent_node                      Parent
              /        \             ===>
     [None, None]    [None, None]
    """
    if tree[0] is not None:
        optimize_tree(tree[0])
    if tree[1] is not None:
        optimize_tree(tree[1])
    if tree[0] == tree[1] == [None, None]:
        tree[0] = tree[1] = None


def invert_tree(tree):
    if not tree[0] and not tree[1]:
        return None

    ret = [None, None]
    if tree[0]:
        ret[0] = invert_tree(tree[0])
    else:
        ret[0] = [None, None]

    if tree[1]:
        ret[1] = invert_tree(tree[1])
    else:
        ret[1] = [None, None]

    if ret == [None, None]:
        return None
    else:
        return ret


def tree_to_network(tree):
    def g(tree, col):
        for direction in (0, 1):
            if tree[direction] is not None:
                if tree[direction] == [None, None]:
                    yield col + [direction]
                else:
                    yield from g(tree[direction], col + [direction])

    return map(bin_to_ip, g(tree, []))


def networks_from_file(ip_file):
    for line in lines(ip_file):
        bin_array = ip_to_bin(line)
        yield bin_array


def strip(s):
    s = s.split(';', maxsplit=1)[0].strip()
    s = s.split('#', maxsplit=1)[0].strip()
    return s


def lines(file_name):
    with open(file_name, 'rt') as f:
        for line in f:
            line = strip(line)
            if line == '':
                continue
            yield line


def main():
    def ip_file_to_js(ip_file, **kwd):
        tree = create_tree(networks_from_file(ip_file))
        optimize_tree(tree)
        return json.dumps(tree, **kwd)

    json_opts = {
        'separators': (',', ':'),
        # 'indent': 4,
    }

    print('var cn_tree = %s;' % ip_file_to_js('./china_ip_list/china_ip_list.txt', **json_opts))
    print('var reserved_tree = %s;' % ip_file_to_js('./china_ip_list/china_ip_list.txt', **json_opts))

    domain_list = list(lines('paper-domains.txt'))
    print('var paper_list = %s;' % json.dumps(domain_list, **json_opts))


if __name__ == '__main__':
    main()
