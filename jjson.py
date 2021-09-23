import json
import string

version = 'v0.0.2'

# 扩展标准 JSON 语法
# 1. 当字符串符合 JavaScript 标识符定义规则时可以不用引号包围以实现解析 js 对象为 Python dict 结构
# 2. 支持 # 行首和行尾注释

# 性能问题:
# 0. 保证只遍历一次输入字符串
# 1. 输入字符串可能非常大,参数以 [s, len(s)] 列表形式传递上下文(大约没什么用,与直接用 str 作为参数一样,但是采用"上下文"打包传送便于以后改进)
# 2. 递归是否会导致堆栈溢出?
# 3. 依然比 json 库慢得多,为什么? 根据 cProfile 分析性能瓶颈可能是 "if c in '0123456789ABCD..' 类似的语句

id_lead_char = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ$_'
id_body_char = id_lead_char + '0123456789'
#id_pat = f"[{id_lead_char}]+[{id_body_char}]*"
number_lead_char = '0123456789+-'
string_lead_char = '\'"'
keywords_map = {"true": True, "false": False, "null": None}
escape_map = {'t': '\t', '\\': '\\', 'n': '\n', 'r': '\r', "'": "'", '"': '"'}

class jjson_decode_error(Exception):
	def __init__(self, s, p):
		self._pos = p

		# 根据 p 定位行列,便于查错
		self._col = 0
		self._row = 0

		for i in range(p):
			if peek(s, i) == '\n':
				self._row += 1
				self._col = 0
			else:
				self._col += 1

	def __str__(self):
		return f"at posion {self._pos} (row {self._row + 1}, col {self._col + 1})"

# 直接访问打包参数的方法
def peek(s, p):
	return s[0][p]

def check(s, p):
	return p < s[1]

# 跳过空白字符和 # 注释,返回下一个有效字符的起始位置 i
def skip_space_comment(s, p):
	while check(s, p):
		if peek(s, p) == '#':
			p = skip_line(s, p)
		elif peek(s, p) in string.whitespace:
			p += 1
		else:
			break
	return p

def skip_line(s, p):
	while check(s, p):
		if peek(s, p) == '\n':
			p += 1
			break
		else:
			p += 1
	return p

# 读取标识符,包括关键字(true, false, null) 返回后需要比对关键字表
def read_id(s, p):
	st_read_id_lead_char = 0
	st_read_id_body_char = 1
	st = 0
	v = ''
	
	while check(s, p):
		c = peek(s, p)
		if st == st_read_id_lead_char:
			if c in id_lead_char:
				v += c
				p += 1
				st = st_read_id_body_char
			else:
				break
		elif st == st_read_id_body_char:
			if c in id_body_char:
				v += c
				p += 1
			else:
				break
		else:
			assert 0
	
	if st == st_read_id_body_char:
		v = keywords_map.get(v, v)
		return p, v
	else:
		raise jjson_decode_error(s, p)

def read_number(s, p):
	st_read_sign = 0
	st_read_base_lead_char = 1
	st_read_base = 2
	st_read_int_lead_char = 3
	st_read_int = 4
	st_read_float = 5
	st_read_science_sign = 6
	st_read_science_float_lead_char = 7
	st_read_science_float = 8
	st = 0
	base = 10
	v = ''

	while check(s, p):
		c = peek(s, p)
		if st == st_read_sign:
			# 读取符号,只允许数字开头字符出现一次
			if c in '-+':
				v += c
				p += 1
			st = st_read_base_lead_char
		elif st == st_read_base_lead_char:
			# 读取进制先导字符 0,其他字符则读取整数部分先导字符
			if c == '0':
				v += c
				p += 1
				st = st_read_base
			else:
				st = st_read_int_lead_char
		elif st == st_read_base:
			# 读取进制标识
			if c in 'xX':
				base = 16
				v += c
				p += 1
				st = st_read_int_lead_char
			elif c in 'oO':
				base = 8
				v += c
				p += 1
				st = st_read_int_lead_char
			elif c in 'bB':
				base = 2
				v += c
				p += 1
				st = st_read_int_lead_char
			else:
				# 此时 v = '+/-0' 所以直接开始读取 10 进制的整数部分
				st = st_read_int
		elif st == st_read_int_lead_char:
			# 检查整数的先导字符(只检查不消费)
			if ((base == 2 and c in '01')
				or (base == 8 and c in '01234567')
				or (base == 10 and c in '0123456789')
				or (base == 16 and c in '0123456789abcdefABCDEF')
			):
				st = st_read_int
			else:
				break
		elif st == st_read_int:
			# 读取整数部分
			if ((base == 2 and c in '01')
				or (base == 8 and c in '01234567')
				or (base == 10 and c in '0123456789.') # 只有 10 进制数字才允许有小数点部分
				or (base == 16 and c in '0123456789abcdefABCDEF')
			):
				if c == '.': st = st_read_float
				v += c
				p += 1
			else:
				break
		elif st == st_read_float:
			# 读取小数部分
			if c in '0123456789Ee':
				if c in 'eE':
					st = st_read_science_sign
				v += c
				p += 1
			else:
				break
		elif st == st_read_science_sign:
			if c in '-+':
				v += c
				p += 1
			st = st_read_science_float_lead_char
		elif st == st_read_science_float_lead_char:
			# E后面自少要跟1位数字
			if c in '0123456789':
				st = st_read_float
			else:
				break
		elif st == st_read_science_float:
			if c in '0123456789':
				v += c
				p += 1
			else:
				break
		else:
			assert 0

	if st == st_read_base:
		return p, 0
	elif st == st_read_int:
		return p, int(v, base)
	elif st in (st_read_float or st, st_read_science_float):
		return p, float(v)
	else:
		raise jjson_decode_error(s, p)

# 遇字符串首字符时调用,中间需要根据 '/" 处理转义
def read_string(s, p):
	st_read_string_lead_char = 0
	st_read_string_body_char = 1
	st = 0
	v = ''
	quote = ''
	esc = False

	while check(s, p):
		c = peek(s, p)
		if st == st_read_string_lead_char:
			if c in string_lead_char:
				quote = c
				p += 1
				st = st_read_string_body_char
			else:
				break
		elif st == st_read_string_body_char:
			if esc:
				v += escape_map.get(c, c)
				p += 1
				esc = False
			elif c == '\\':
				esc = True
				p += 1
			elif c == quote:
				# 只有遇到对应的引号才算成功结束
				p += 1
				return p, v
			else:
				v += c
				p += 1
		else:
			assert 0
	raise jjson_decode_error(s, p)

def read_list(s, p):
	st_read_list_lead_char = 0
	st_read_list_item_or_end_char = 1
	st_read_list_item = 2
	st_read_list_sep_or_end_char = 3
	st = 0
	v = []

	while check(s, p):
		c = peek(s, p)
		if st == st_read_list_lead_char:
			if c == '[':
				p += 1
				p = skip_space_comment(s, p)
				st = st_read_list_item_or_end_char
			else:
				break
		elif st == st_read_list_item_or_end_char:
			if c == ']':
				p += 1
				return p, v
			else:
				st = st_read_list_item
		elif st == st_read_list_item:
			p, i = read(s, p)
			v.append(i)

			p = skip_space_comment(s, p)
			st = st_read_list_sep_or_end_char
		elif st == st_read_list_sep_or_end_char:
			if c == ',':
				p += 1
				p = skip_space_comment(s, p)
				st = st_read_list_item
			elif c == ']':
				p += 1
				return p, v
			else:
				break
		else:
			assert 0
	raise jjson_decode_error(s, p)

def read_dict(s, p):
	st_read_dict_lead_char = 0
	st_read_dict_key_or_end_char = 1
	st_read_dict_key = 2
	st_read_dict_kv_sep_char = 3
	st_read_dict_val = 4
	st_read_dict_sep_or_end_char = 5
	st = 0
	v = {}
	key, val = None, None

	while check(s, p):
		c = peek(s, p)
		if st == st_read_dict_lead_char:
			if c == '{':
				p += 1
				p = skip_space_comment(s, p)
				st = st_read_dict_key_or_end_char
			else:
				break
		elif st == st_read_dict_key_or_end_char:
			if c == '}':
				p += 1
				return p, v
			else:
				st = st_read_dict_key
		elif st == st_read_dict_key:
			p, key = read(s, p)
			p = skip_space_comment(s, p)
			st = st_read_dict_kv_sep_char
		elif st == st_read_dict_kv_sep_char:
			if c == ':':
				p += 1
				p = skip_space_comment(s, p)
				st = st_read_dict_val
			else:
				break
		elif st == st_read_dict_val:
			p, val = read(s, p)
			v[key] = val

			p = skip_space_comment(s, p)
			st = st_read_dict_sep_or_end_char
		elif st == st_read_dict_sep_or_end_char:
			if c == ',':
				p += 1
				p = skip_space_comment(s, p)
				st = st_read_dict_key
			elif c == '}':
				p += 1
				return p, v
			else:
				break
		else:
			assert 0
	raise jjson_decode_error(s, p)

def read(s, p):
	p = skip_space_comment(s, p)
	if check(s, p):
		c = peek(s, p)
		if c == '[': return read_list(s, p)
		elif c == '{': return read_dict(s, p)
		elif c in string_lead_char: return read_string(s, p)
		elif c in number_lead_char: return read_number(s, p)
		elif c in id_lead_char: return read_id(s, p)
	raise jjson_decode_error(s, p)

def loads(s, return_pos = False):
	p, v = read([s, len(s), 0], 0)
	if return_pos: return p, v
	else: return v

def load(fn, return_pos = False, encoding = 'utf-8'):
	with open(fn, "r", encoding = encoding) as fd:
		return loads(fd.read(), return_pos)

def dumps(*args, **kwargs):
	return json.dumps(*args, **kwargs)

def dump(*args, **kwargs):
	return json.dump(*args, **kwargs)
