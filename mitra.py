from parsers import *
import random
import sys
import hashlib
import os.path
from args import *

PARSERS = [
	pdf,
	zip_,
]

def randbuf(length):
	res = b"\0" * length
	res = bytes([random.randrange(255) for i in range(length)])
	return res

def separatePayloads(fn, exts, data, swaps, overlap):
	NoFile, SplitDir = getVars(["NOFILE", "SPLITDIR"])

	ext1, ext2 = exts
	p1 = b""
	p2 = b""
	start = 0
	for end in swaps:
		p1 += data[start:end]
		p2 += randbuf(end-start)

		start = end
		p1, p2 = p2, p1
	p1 += data[end:]
	p2 += randbuf(len(data)-end)

	p2 = overlap + p2[len(overlap):]

	if not NoFile:
		with open(os.path.join(SplitDir, "%s.%s" % (fn, ext1)), "wb") as f:
				f.write(p1)
		with open(os.path.join(SplitDir, "%s.%s" % (fn, ext2)), "wb") as f:
				f.write(p2)
	return

def writeFile(name, exts, data, swaps=[], overlap=b""):
	OutDir, NoFile, Split = getVars(["OUTDIR", "NOFILE", "SPLIT"])

	random.seed(0)
	hash = hashlib.sha256(data).hexdigest()[:8].lower()

	if Split and swaps != []:
		separatePayloads(name, exts, data, swaps, overlap)
	fn = "%s.%s.%s" % (name, hash, ".".join(exts))
	if not NoFile:
		with open(os.path.join(OutDir, "%s" % fn), "wb") as f:
				f.write(data)
	return

def isStackOk(ftype1, ftype2):
	# d# print("Stack: %s-%s" % (ftype1.TYPE, ftype2.TYPE))
	result = True
	if not ftype1.bAppData:
		# d# print("! File type 1 (%s) doesn't support appended data." % (ftype1.TYPE))
		result = False

	if ftype2.start_o == 0:
		# d# print("! File type 2 (%s) starts at offset 0 - it can't be appended." % (ftype2.TYPE))
		return False
	else:
		len1 = len(ftype1.data)
		if len1 >= ftype2.start_o:
			# d# print("! File 1 is too big (0x%X). File 2 should start at offset 0x%X or less." % (len1, ftype2.start_o) )
			result = False

	return result

def isCavOk(ftype1, ftype2):
	# d# print("Cavity: %s_%s" % (ftype1.TYPE, ftype2.TYPE))
	filling = ftype1.data
	filling_l = len(ftype1.data)

	result = True
	if not ftype1.bAppData:
		# d# print("! File type 1 (%s) doesn't support appended data." % (ftype1.TYPE))
		result = False

	if not ftype2.precav_s:
		# d# print("! File type 2 (%s) doesn't start with any cavity." % (ftype2.TYPE))
		return False
	elif filling_l > ftype2.precav_s:
		# d# print("! File 1 is too big (0x%X). File 2's cavity is only 0x%X." % (filling_l, ftype2.precav_s) )
		result = False

	return result

def isParasiteOk(ftype1, ftype2):
	# d# print("Parasite: %s[%s]" % (ftype1.TYPE, ftype2.TYPE))
	result = True
	if not ftype1.bParasite:
		# d# print("! File type 1 (%s) doesn't support parasites." % (ftype1.TYPE))
		return False

	# start_o is 0 when precav_s isn't
	if (ftype1.parasite_o > ftype2.start_o + ftype2.precav_s):
		# d# print("! File type 1 (%s) can only host parasites at offset 0x%X. File 2 should start at offset 0x%X or less." % (ftype1.TYPE, ftype1.parasite_o, ftype2.start_o) )
		result = False

	if ftype1.parasite_s < len(ftype2.data):
		# d# print("! File type 1 (%s) can accept parasites only of size 0x%X max. File 2 is too big (%X)." % (ftype1.TYPE, ftype1.parasite_s, len(ftype2.data)) )
		result = False

	return result

def isZipperOk(ftype1, ftype2):
	# d# print("Zipper: %s^%s" % (ftype1.TYPE, ftype2.TYPE))
	result = True
	if not ftype1.bZipper:
		# d# print("! File type 1 (%s) doesn't support zippers." % (ftype1.TYPE))
		return False
#  if not ftype1.bAppData:
#    # d# print("! File type 1 (%s) doesn't support appended data." % (ftype1.TYPE))
#    result = False

	if not ftype1.bParasite:
		# d# print("! File type 1 (%s) doesn't support parasites." % (ftype1.TYPE))
		return False

	if not ftype2.bParasite:
		# d# print("! File type 2 (%s) doesn't support parasites." % (ftype2.TYPE))
		return False

	return result

def Hit(type1, type2):
	global VERBOSE
	if getVar("VERBOSE"):
		# d# print("HIT " + ";".join(sorted([type1, type2])))
		pass

def Stack(ftype1, ftype2, fn1, fn2):
	if isStackOk(ftype1, ftype2):
		# print(("Stack: concatenation of File1 (type %s) and File2 (type %s)" % (ftype1.TYPE, ftype2.TYPE)))
		# appData = ftype2.fixformat(ftype2.data, len(ftype1.data)) # alignments / padding?
		appData = ftype2.data
		swap_o = len(ftype1.data +
			ftype1.wrappend(b""))

		Hit(ftype1.TYPE, ftype2.TYPE)
		writeFile(
			"S(%x)-%s-%s" % (swap_o, ftype1.TYPE, ftype2.TYPE),
			[ext(fn2), ext(fn1)],
			ftype1.data +
			ftype1.wrappend(appData),
			[swap_o]
		)

def Parasite(ftype1, ftype2, fn1, fn2):
	if isParasiteOk(ftype1, ftype2):
		pass
		# print(("Parasite: hosting of File2 (type %s) in File1 (type %s)" % (ftype2.TYPE, ftype1.TYPE)))
		# host file may have to validate parasite contents
		parasitized, swaps = ftype1.parasitize(ftype2)
		if parasitized is None:
			return

		# TODO: make this for all layouts ?
		# Optional alignment via wrappending
		filealig = len(parasitized) % 16
		if getVar("AESGCM") and filealig > 0:
			# we need to know which sides wrappends
			wrap = ftype1
			if len(ftype2.wrappend(b"")) != 0:
				wrap = ftype2

			for i in range(17, 32):
				aligned = parasitized + wrap.wrappend(b"\0" * i)
				if len(aligned) % 16 == 0:
					break
			if wrap == ftype2:
				swaps += [len(parasitized)] # before wrappending
			parasitized = aligned


		swapstr = "(%s)" % "-".join("%x" % s for s in swaps) if swaps != [] else ""
		Hit(ftype1.TYPE, ftype2.TYPE)
		writeFile(
			"P%s-%s[%s]" % (swapstr, ftype1.TYPE, ftype2.TYPE),
			[ext(fn1), ext(fn2)],
			parasitized,
			swaps
		)

def Zipper(ftype1, ftype2, fn1, fn2):
	if isZipperOk(ftype1, ftype2):
		# host file may have to validate parasite contents
		# appData = ftype2.fixformat(len(ftype1.data)) # alignments / padding?
		# parasite = ftype2.fixformat(ftype1.parasite_o)
		zipper, swaps = ftype1.zipper(ftype2)
		if (zipper, swaps) == (None, []):
			return
		# print(("Zipper: interleaving of File1 (type %s) and File2 (type %s)" % (ftype1.TYPE, ftype2.TYPE)))
		swapstr = "(%s)" % "-".join("%x" % s for s in swaps) if swaps != [] else ""
		Hit(ftype1.TYPE, ftype2.TYPE)
		writeFile(
			"Z%s-%s^%s" % (swapstr, ftype1.TYPE, ftype2.TYPE),
			[ext(fn1), ext(fn2)],
			zipper,
			swaps
		)

def Cavity(ftype1, ftype2, fn1, fn2):
	if isCavOk(ftype1, ftype2):
		# print(("Cavity: File1 (type %s) into File2 (type %s)" % (ftype1.TYPE, ftype2.TYPE)))

		# TODO: requires any normalization ?
		filling = ftype1.data
		filling_l = len(filling + ftype1.wrappend(b"")) # FIXME: variable length not supported
		filled = filling + ftype1.wrappend(ftype2.data[filling_l:])
		swap = filling_l
		Hit(ftype1.TYPE, ftype2.TYPE)
		writeFile(
			"C(%x)-%s-%s" % (swap, ftype1.TYPE, ftype2.TYPE),
			[ext(fn2), ext(fn1)],
			filled,
			[swap]
		)

def JpegOver5(jpeg, other, swaps, overlap):
	"""pre-process JPEG to require only 5 bytes of overlap instead of 6

	Store the incremented higher nibble
	 and the other lower nibble
	Grow the parasite by the minimal amount - up to 0x100 alignment
	The parasite requires further growing on post-processing
	 depending on the other lower nibble after encryption once the nonce is known.

	Parameters
  ----------
	jpeg: data buffer
		the JPEG file data with a parasite

	other: data buffer
		the other original file

	swaps: list of int
		where data swaps its origin in the final polyglot

	overlap: list of bytes
		values of overlapping bytes in the other file - should start like `other`
	"""
	highnib = jpeg[4]
	lownib = jpeg[5]
	offset = 4 + 0x100*highnib + lownib

	if highnib == 0xff                 \
		or not other.startswith(overlap) \
		or len(swaps) != 2               \
		or swaps[0] != 6                 \
		or len(overlap) != 6:
		return jpeg, swaps, overlap

	othernib = other[5]

	delta = 0x100 - lownib

	swaps[0] -= 1     # saved one byte
	swaps[1] += delta # padding

	overlap = overlap[:-1]

	jpeg = b"".join([
		jpeg[:4],             # 00-03: the original JPG header
		bytes([highnib + 1]), #   04: 0x100-padded parasite length
		bytes([othernib]),    #   05: but storing the other byte for later
		jpeg[6:offset],       # the previous parasite
		delta*b"\0",          #  with 0x100-padding
		jpeg[offset:],        # the rest of the JPEG
		])

	# d# print("Jpeg overlap file: reducing one byte")
	# d# print("  (don't forget to postprocess after bruteforcing)")
	return jpeg, swaps, overlap

def JpegOver4(jpeg, other, swaps, overlap):
	"""pre-process JPEG to require only 4 bytes of overlap instead of 6

	Writes the 2 last byte of the overlap on the file.
	Remove them from the file name.
	Decrement the first split from the file name.
	"""
	if not other.startswith(overlap) \
		or len(swaps) != 2             \
		or swaps[0] != 6               \
		or len(overlap) != 6:
		return jpeg, swaps, overlap

	offset = swaps[-1]
	swaps[0] -= 2
	overlap = overlap[:-2]

	jpeg = b"".join([
		jpeg[:4],      # 00-03: the original JPG header
		other[4:6],    #   04: 0x100-padded parasite length
		jpeg[6:],      # the previous parasite
		])

	# d# print("Jpeg overlap file: reducing two bytes")
	# d# print("  (don't forget to postprocess after bruteforcing)")
	return jpeg, swaps, overlap

def Overlap(ftype1, ftype2, fn1, fn2, THRESHOLD=6):
	# d# print("Overlapping parasite")
	if not ftype1.bParasite:
		# d# print("! Parasite not supported.", ftype1.TYPE)
		return False
	ftype1.getCut()
	overlap_l = ftype1.parasite_o
	if overlap_l is None:
		# print("! Error - overlap is None", ftype1.TYPE)
		return False
	if overlap_l > THRESHOLD:
		# d# print("! Overlap (length:%i) too long (threshold:%i)." % (overlap_l, THRESHOLD))
		return False

	fextra = blob.reader(ftype2.data[overlap_l:])
	parasitized, swaps = ftype1.parasitize(fextra)
	if parasitized is None:
		return False

	overlap = ftype2.data[:overlap_l]

	# if it's a JPEG overlap, we can reduce the overlap by one byte
	# by abusing the lower nibble of the comment length to match the other type content
	# but this file is not a valid JPEG as is
	# the comment is padded to 0x100 alignment,
	# but the lowest nibble is the other byte before encryptions (w/ unknown nonce at this stage).
	if ftype1.TYPE == "JPG":
		parasitized, swaps, overlap = JpegOver4(parasitized, ftype2.data, swaps, overlap)

	overlap_s = "".join("%02X" % c for c in overlap)
	swapstr = "(%s)" % "-".join("%x" % s for s in swaps) if swaps != [] else ""
	Hit(ftype1.TYPE, ftype2.TYPE)
	writeFile(
		"O%s-%s[%s]{%s}" % (swapstr, ftype1.TYPE, ftype2.TYPE, overlap_s),
		[ext(fn1), ext(fn2)],
		parasitized,
		swaps=swaps,
		overlap=overlap,
	)
	# print("Generic overlapping polyglot file created.")
	return True

def OverlapPE(ftype1, ftype2, fn1, fn2):
	# reverse overlap:
	# ftype1 parasitize even if it's ftype2 defining the length
	# Only applies to PE so far.

	SIG_l = 2        # `MZ` required at 0
	ELFANEW_o = 0x3c # Offset of first required information

	if not ftype2.TYPE.startswith("PE"):
		return False
	overlap_l = SIG_l

	# d# print("PE Reverse overlapping parasite")
	if not ftype1.bParasite:
		return False
	if ftype1.parasite_o is None:
		# d# print("! Error - overlap is None", ftype1.TYPE)
		return False
	cut = ftype1.getCut()
	if ftype1.parasite_o > ELFANEW_o:
		# d# print("! Parasite offset too far: type (%s) parasite offset (0x%X)" % (ftype1.TYPE, ftype1.parasite_o))
		return False
	if len(ftype2.data) > ftype1.parasite_s:
		# d# print("! PE file (size:%i) can't fit in parasite (max: %i)." % (len(ftype2.data), ftype1.parasite_s))
		return False

	#FIXME still buggy with: BPG CPIO WASM (wrong offset computation)
	fextra = blob.reader(ftype2.data[ftype1.parasite_o:])
	parasitized, swaps = ftype1.parasitize(fextra)

	if parasitized is None:
		return False

	overlap = ftype2.data[:overlap_l]
	overlap_s = "".join("%02X" % c for c in overlap)
	swapstr = "(%s)" % "-".join("%x" % s for s in swaps) if swaps != [] else ""
	Hit(ftype1.TYPE, ftype2.TYPE)
	writeFile(
		"OR%s-%s[%s]{%s}" % (swapstr, ftype1.TYPE, ftype2.TYPE, overlap_s),
		[ext(fn1), ext(fn2)],
		parasitized,
		swaps=swaps,
		overlap=overlap,
	)
	# print("Specific PE overlapping polyglot file created.")
	return True

def OverlapAll(ftype1, ftype2, fn1, fn2):
	OverlapPE(ftype1, ftype2, fn1, fn2)
	Overlap(ftype1, ftype2, fn1, fn2)

ext = lambda s:s[s.rfind(".")+1:]

def DoAll(ftype1, ftype2, fn1, fn2):
	Stack(ftype1, ftype2, fn1, fn2)
	Parasite(ftype1, ftype2, fn1, fn2)
	Zipper(ftype1, ftype2, fn1, fn2)
	Cavity(ftype1, ftype2, fn1, fn2)
	if getVar("OVERLAP"):
		OverlapAll(ftype1, ftype2, fn1, fn2)
