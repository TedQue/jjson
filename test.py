#!/usr/bin/env python3
import jjson

if __name__ == "__main__":
	print(f"Welcome to jjson version {jjson.version} by Que's C++ Studio")

	print("\ntest read number: ")
	print(jjson.loads("123"))
	print(jjson.loads("-3.14"))
	print(jjson.loads("0x1F"))
	print(jjson.loads("1.23E-04"))

	print("\ntest read string: ")
	print(jjson.loads("abc"))
	print(jjson.loads("\"a'b\\\"c\""))

	print("\ntest read javascript id: ")
	print(jjson.loads("id"))
	print(jjson.loads("$id"))
	print(jjson.loads("true"))
	print(jjson.loads("null"))

	print("\ntest read list: ")
	print(jjson.loads("[]"))
	print(jjson.loads("[1, 'a', $id]"))

	print("\ntest read dict: ")
	print(jjson.loads("{}"))
	print(jjson.loads("{'key': 'value', 'key_list': []}"))

	print("\ntest read configure file with comment: example.conf")
	print(jjson.load("example.conf"))

	print("\ntest read js object: example.js")
	print(jjson.load("example.js"))

