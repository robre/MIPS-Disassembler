#!/usr/bin/python3
#-*- coding: utf-8 -*-
# 
# author: robrt
#
# 7.2.14
#
# a MIPS - assembly language disassembler.
# this program will take a mips binary as argument
# in a special format as
# 0x00400000 0x20080000
# 0x00400004 0x20090001
# ...
# ...
# 0x0040001c 0x01001020
# ...
# etc
#
# whereas at the left side we have the adresses in hex 
# and on the right side the instructions.
# the disassembler will return the cleartext MIPS instructions with their corresponding addresses

__version__ = 1.0

enc = "utf-8"

import sys

# Dictionary for the opcodes
# 0 and 1 have special meaning and do not directly define the function
opcodes = {
	0:"rtyp",
	1:"branch",
	2:"j",
	3:"jal",
	4:"beq",
	5:"bne",
	6:"blez",
	7:"bgtz",
	8:"addi",
	10:"slti",
	12:"andi",
	13:"ori",
	14:"xori",
	15:"lui",
	32:"lb",
	35:"lw",
	40:"sb",
	43:"sw"
	}

# if we have a r-type instruction (opcode 0), we need the function codes to decode the functions
fcodes = { 
	0:"sll",
	2:"slr",
	3:"sra",
	4:"sllv",
	6:"srlv",
	7:"srav",
	8:"jr",
	9:"jalr",
	12:"syscall",
	13:"break",
	16:"mfhi",
	17:"mtlo",
	18:"mflo",
	19:"mtlo",
	24:"mult",
	26:"div",
	32:"add",
	34:"sub",
	36:"and",
	37:"or",
	38:"xor",
	39:"nor",
	42:"slt"
	}

# List of registernumbers and their cleartext names
registers = {
	0:"$zero",
	1:"$at",
	2:"$v0",
	3:"$v1",
	4:"$a0",
	5:"$a1",
	6:"$a2",
	7:"$a3",
	8:"$t0",
	9:"$t1",
	10:"$t2",
	11:"$t3",
	12:"$t4",
	13:"$t5",
	14:"$t6",
	15:"$t7",
	16:"$s0",
	17:"$s1",
	18:"$s2",
	19:"$s3",
	20:"$s4",
	21:"$s5",
	22:"$s6",
	23:"$s7",
	24:"$t8",
	25:"$t9",
	26:"$k0",
	27:"$k1",
	28:"$gp",
	29:"$sp",
	30:"$fp",
	31:"$ra"
}


# Masks for getting the different parts out of the machinecode, by and'ing the code with the mask and shifting back
rTypeMasks = {
	"opcode":0b11111100000000000000000000000000,
	"rs"    :0b00000011111000000000000000000000,
	"rt"    :0b00000000000111110000000000000000,
	"rd"    :0b00000000000000001111100000000000,
	"shamd" :0b00000000000000000000011111000000,
	"funct" :0b00000000000000000000000000111111}

iTypeMasks = {
	"opcode":0b11111100000000000000000000000000,
	"rs"    :0b00000011111000000000000000000000,
	"rt"    :0b00000000000111110000000000000000,
	"imm"	:0b00000000000000001111111111111111}
jTypeMasks = {
	"opcode":0b11111100000000000000000000000000,
	"addr"	:0b00000011111111111111111111111111}

# disassemble(32-bit int instruction) -> Instruction (string)

def zk(zahl): # 16 bit immedieates, calculate 2-compliment
	msb = zahl >> 15 # most significant bit, indicates if negative or positiv
	if(msb==0):
		return zahl
	else:
		return -2**16 + ((zahl << 1) >> 1)


def disassemble(instruction, pc):
	command = ""
	a = instruction
	opcode = (a & 0b11111100000000000000000000000000) >> (32-6) #get opcode

	if opcode not in opcodes:
		return "error"
	elif (opcode == 0): # Rtype instruction
		fcode = a & rTypeMasks["funct"] # get functioncode
		if fcode not in fcodes:
			return "error"
		else:
			rs = registers[(a & rTypeMasks["rs"]) >> 21]
			rt = registers[(a & rTypeMasks["rt"]) >> 16]
			rd = registers[(a & rTypeMasks["rd"]) >> 11]
			if(fcode==0 or fcode==2 or fcode==3): # shift instructions
				shamd = (a & rTypeMasks["shamd"]) >> 6
				return fcodes[fcode] + " " + rd + "," + rt + "," + str(shamd)
			elif(fcode==8 or fcode==9): # jr/jalr
				return fcodes[fcode] + " " + rs
			elif(fcode==12 or fcode==13):#syscall or break
				return fcodes[fcode]
			elif(fcode==16 or fcode==17 or fcode == 18 or fcode == 19):
				# mfhi, mthi, mflo, mtlo
				return fcodes[fcode] + " " + rd
			elif(fcode==24 or fcode==26): # mult and div
				return fcodes[fcode] + " " + rs + "," + rt
			else:
				return fcodes[fcode] + " " + rd + "," + rs + "," + rt
				
				


	elif (opcode == 1):
		rt = (a & 0b00000000000111110000000000000000) >> 16
		rs = registers[(a & 0b00000011111000000000000000000000) >> 21]
		imm = (a & iTypeMasks["imm"])
		if(rt==0): # depends on rt
			return "bltz " + rs + "," + str(hex(imm))
		elif(rt==1):
			return "bgez " + rs + "," + str(hex(imm))

	elif (opcode == 2 or opcode == 3):
		# j/jal j-type instructions
		addr = (a & jTypeMasks["addr"]) << 2 # get deleted parts of the number back
		return opcodes[opcode] + " " + str(hex(addr))
	elif (opcode == 15): # lui we need adress displayed nicely not in 2k
		rt  = registers[(a & iTypeMasks["rt"]) >> 16]
		imm = (a & iTypeMasks["imm"])
		return opcodes[opcode] + " " + rt + str(hex(imm))
	elif (opcode == 32 or opcode == 35 or opcode == 40 or opcode== 43): # lw lb sb sw
		rt = registers[(a & 0b00000000000111110000000000000000) >> 16]
		rs = registers[(a & 0b00000011111000000000000000000000) >> 21]
		imm = (a & iTypeMasks["imm"])
		if(imm>=0x8000):
			return  opcodes[opcode] + " " + rt + "," + str(hex(imm)) + "(" + rs + ")"
		else:
			return opcodes[opcode] + " " + rt + "," + str(zk(imm)) + "(" + rs + ")"
	
	else:
		rs  = registers[(a & iTypeMasks["rs"]) >> 21]
		rt  = registers[(a & iTypeMasks["rt"]) >> 16]
		imm = (a & iTypeMasks["imm"]) # 4*off + 4
		if(opcode==4 or opcode==5 or opcode ==6 or opcode==7):# if we got branches, the offset has to be calked
			return opcodes[opcode]  + " " + rt + "," + rs + "," + str(hex(imm*4+4+pc))
		return opcodes[opcode] + " " + rt + "," + rs + "," + str(zk(imm))


def main():
	with open(sys.argv[1], 'r') as f:
		for line in f:
			n = line.split(' ')
			x = n[1].split('0x')[1]
			m = n[0].split('0x')[1]
			print(n[0] + " " + disassemble(int(x,16),int(m,16)))	
if __name__=='__main__':
	if (len(sys.argv) < 2):
		print("""Python disassembler\nUsage: """ + sys.argv[0] + """ [filepath]""")
	else:
		main()



