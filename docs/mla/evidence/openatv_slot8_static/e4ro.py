#!/usr/bin/env python3
"""Read-only ext4 reader (no mount, no write): opens the block device O_RDONLY and walks the on-disk structures.
usage: e4ro.py <device> ls <path> | cat <path> | tar <path> [<path> ...]   (tar -> stdout, regular files + dirs + symlinks)
Used to inspect another multiboot slot's root directory while it is not running."""
import os, struct, sys, tarfile, io, stat, time

class FS:
	def __init__(self, dev):
		self.fd = os.open(dev, os.O_RDONLY)
		sb = self.pread(1024, 1024)
		self.inodes_count, = struct.unpack_from("<I", sb, 0)
		self.log_bs, = struct.unpack_from("<I", sb, 24)
		self.bs = 1024 << self.log_bs
		self.blocks_per_group, = struct.unpack_from("<I", sb, 32)
		self.inodes_per_group, = struct.unpack_from("<I", sb, 40)
		magic, = struct.unpack_from("<H", sb, 56)
		assert magic == 0xEF53, "not ext2/3/4"
		self.inode_size, = struct.unpack_from("<H", sb, 88)
		self.feat_incompat, = struct.unpack_from("<I", sb, 96)
		self.first_data_block, = struct.unpack_from("<I", sb, 20)
		self.is64 = bool(self.feat_incompat & 0x80)
		self.desc_size = struct.unpack_from("<H", sb, 254)[0] if self.is64 else 32
		if not self.desc_size:
			self.desc_size = 32
		self.gdt = (self.first_data_block + 1) * self.bs
	def pread(self, off, n):
		return os.pread(self.fd, n, off)
	def inode(self, ino):
		g, idx = divmod(ino - 1, self.inodes_per_group)
		d = self.pread(self.gdt + g * self.desc_size, self.desc_size)
		lo, = struct.unpack_from("<I", d, 8)
		hi = struct.unpack_from("<I", d, 0x28)[0] if self.is64 and self.desc_size >= 64 else 0
		table = (hi << 32) | lo
		return self.pread(table * self.bs + idx * self.inode_size, self.inode_size)
	def meta(self, raw):
		mode, = struct.unpack_from("<H", raw, 0)
		size_lo, = struct.unpack_from("<I", raw, 4)
		size_hi, = struct.unpack_from("<I", raw, 108)
		mtime, = struct.unpack_from("<I", raw, 16)
		flags, = struct.unpack_from("<I", raw, 32)
		return mode, (size_hi << 32) | size_lo, mtime, flags
	def blocks(self, raw):
		"""list of (logical, physical, count)"""
		mode, size, mtime, flags = self.meta(raw)
		ib = raw[40:100]
		if flags & 0x80000:  # extents
			return self._extents(ib)
		out = []
		ptrs = struct.unpack_from("<15I", ib)
		n = (size + self.bs - 1) // self.bs
		per = self.bs // 4
		def ind(blk, depth):
			if not blk:
				return []
			arr = struct.unpack("<%dI" % per, self.pread(blk * self.bs, self.bs))
			if depth == 1:
				return list(arr)
			r = []
			for b in arr:
				r += ind(b, depth - 1) if b else [0] * (per ** (depth - 1))
			return r
		lst = list(ptrs[:12]) + ind(ptrs[12], 1) + ind(ptrs[13], 2) if n > 12 else list(ptrs[:12])
		if n > 12 + per + per * per:
			lst += ind(ptrs[14], 3)
		for i, b in enumerate(lst[:n]):
			if b:
				out.append((i, b, 1))
		return out
	def _extents(self, node):
		magic, entries, mx, depth = struct.unpack_from("<HHHH", node, 0)
		assert magic == 0xF30A
		out = []
		for e in range(entries):
			off = 12 + e * 12
			if depth == 0:
				lblk, ln, shi, slo = struct.unpack_from("<IHHI", node, off)
				if ln > 32768:  # uninitialized extent: zeros
					continue
				out.append((lblk, (shi << 32) | slo, ln))
			else:
				lblk, llo, lhi = struct.unpack_from("<IIH", node, off)
				child = (lhi << 32) | llo
				out += self._extents(self.pread(child * self.bs, self.bs))
		return out
	def data(self, raw):
		mode, size, mtime, flags = self.meta(raw)
		if flags & 0x10000000:  # inline data
			return raw[40:100][:size]
		buf = bytearray(size)
		for lblk, pblk, cnt in self.blocks(raw):
			start = lblk * self.bs
			if start >= size:
				continue
			n = min(cnt * self.bs, size - start)
			buf[start:start + n] = self.pread(pblk * self.bs, n)
		return bytes(buf)
	def readdir(self, ino):
		d = self.data(self.inode(ino))
		out, p = [], 0
		while p + 8 <= len(d):
			inum, rec, nlen, ftype = struct.unpack_from("<IHBB", d, p)
			if rec < 8:
				break
			if inum:
				name = d[p + 8:p + 8 + nlen].decode("utf-8", "replace")
				if name not in (".", ".."):
					out.append((name, inum))
			p += rec
		return out
	def lookup(self, path, follow=True, depth=0):
		ino = 2
		parts = [x for x in path.split("/") if x]
		for i, part in enumerate(parts):
			ents = dict(self.readdir(ino))
			if part not in ents:
				raise FileNotFoundError(path)
			ino = ents[part]
			raw = self.inode(ino)
			mode = self.meta(raw)[0]
			if stat.S_ISLNK(mode) and (follow or i < len(parts) - 1) and depth < 8:
				tgt = self.readlink(raw)
				base = "/".join(parts[:i]) if not tgt.startswith("/") else ""
				return self.lookup(base + "/" + tgt + "/" + "/".join(parts[i + 1:]), follow, depth + 1) if not tgt.startswith("/") else self.lookup(ROOT + tgt + "/" + "/".join(parts[i + 1:]), follow, depth + 1)
		return ino
	def readlink(self, raw):
		mode, size, mtime, flags = self.meta(raw)
		if size < 60 and not flags & 0x80000:
			return raw[40:40 + size].decode("utf-8", "replace")
		return self.data(raw).decode("utf-8", "replace")

ROOT = ""  # slot root inside the partition (absolute symlinks of the slot resolve under it)

def main():
	global ROOT
	dev, cmd = sys.argv[1], sys.argv[2]
	args = sys.argv[3:]
	if cmd == "--root":
		ROOT, cmd, args = args[0].rstrip("/"), args[1], args[2:]
	fs = FS(dev)
	if cmd == "ls":
		for name, ino in sorted(fs.readdir(fs.lookup(ROOT + args[0]))):
			mode, size, mtime, flags = fs.meta(fs.inode(ino))
			print("%s %10d %s %s" % (stat.filemode(mode), size, time.strftime("%Y-%m-%d %H:%M", time.gmtime(mtime)), name))
	elif cmd == "cat":
		sys.stdout.buffer.write(fs.data(fs.inode(fs.lookup(ROOT + args[0]))))
	elif cmd == "tar":
		tf = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
		def add(path, ino):
			raw = fs.inode(ino)
			mode, size, mtime, flags = fs.meta(raw)
			ti = tarfile.TarInfo(path.lstrip("/"))
			ti.mtime, ti.mode = mtime, stat.S_IMODE(mode)
			if stat.S_ISDIR(mode):
				ti.type = tarfile.DIRTYPE
				tf.addfile(ti)
				for name, child in sorted(fs.readdir(ino)):
					add(path + "/" + name, child)
			elif stat.S_ISLNK(mode):
				ti.type, ti.linkname = tarfile.SYMTYPE, fs.readlink(raw)
				tf.addfile(ti)
			elif stat.S_ISREG(mode):
				d = fs.data(raw)
				ti.size = len(d)
				tf.addfile(ti, io.BytesIO(d))
		for p in args:
			add(p, fs.lookup(ROOT + p, follow=False))
		tf.close()

main()
