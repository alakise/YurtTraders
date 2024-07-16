import ast
import operator as op
import re

from web3 import Web3

from bsc_blockchain import BSCBlockchain


class Operations:

    def __init__(self, blockchain):
        self.blockchain = blockchain
        pass

    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                 ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                 ast.USub: op.neg}

    def alphabet_to_letter(self, message: str):
        message = message.replace("1st", 'first')
        message = message.replace("2nd", 'second')
        message = message.replace("3rd", 'third')
        message = message.replace("4th", 'fourth')
        message = message.replace("5th", 'fifth')
        message = message.replace("6th", 'sixth')
        message = message.replace("f1rst", 'first')
        message = message.replace("third", 'third')
        message = message.replace("f1fth", 'fifth')
        message = message.replace("s1xth", 'sixth')
        message = message.replace("the ", '')
        message = message.replace("of ", '')
        message = message.replace("letter ", '')
        message = message.replace("first alphabet", "a")
        message = message.replace("second alphabet", "b")
        message = message.replace("third alphabet", "c")
        message = message.replace("fourth alphabet", "d")
        message = message.replace("fifth alphabet", "e")
        message = message.replace("sixth alphabet", "f")
        return message

    def analyse_message(self, message: str):
        # basic cleaning
        message = message.lower()
        message = message.replace("00000000", '')
        message = message.replace("dead", '')
        message = re.sub(
            r'(?:🔴|🟥|❌|❎|fake|honeypot|incorrect|wrong|scam)+[ \-*:|]*(?:ca|contract|address)*[ \-*:|]*0x[a-fA-F0-9]+',
            '', message)
        message = self.alphabet_to_letter(message)
        message = self.word_to_number(message)
        message = self.clean_shit(message)
        result = self.do_math(message)
        if result:
            return result
        print("Math result failed.")

        result = self.remove_everything_and_try(message)
        if result:
            return result
        print("Remove everything failed.")

        return self.glue_operation(message)

    def clean_shit(self, message: str):
        message = message.replace('you', '')
        message = message.replace('can\'t', '')
        message = message.replace('snipe', '')
        message = message.replace('me', '')
        message = message.replace('this', '')
        message = message.replace('sniper', '')
        message = message.replace('(remove)', '')
        message = message.replace('( remove )', '')
        message = message.replace('remove', '')
        return message

    @staticmethod
    def morse_alphabet(message):
        if 'morse' in message:
            morse_code_dict = {'A': '.-', 'B': '-...',
                           'C': '-.-.', 'D': '-..', 'E': '.',
                           'F': '..-.', 'G': '--.', 'H': '....',
                           'I': '..', 'J': '.---', 'K': '-.-',
                           'L': '.-..', 'M': '--', 'N': '-.',
                           'O': '---', 'P': '.--.', 'Q': '--.-',
                           'R': '.-.', 'S': '...', 'T': '-',
                           'U': '..-', 'V': '...-', 'W': '.--',
                           'X': '-..-', 'Y': '-.--', 'Z': '--..',
                           '1': '.----', '2': '..---', '3': '...--',
                           '4': '....-', '5': '.....', '6': '-....',
                           '7': '--...', '8': '---..', '9': '----.',
                           '0': '-----', ', ': '--..--', '.': '.-.-.-',
                           '?': '..--..', '/': '-..-.', '-': '-....-',
                           '(': '-.--.', ')': '-.--.-', ':': '---...',
                               '+': '.-.-.'
                           }
            # extra space added at the end to access the
            # last morse code
            message += ' '

            decipher = ''
            citext = ''
            for letter in re.findall('(?:[-.] ?){10,5000}', message)[0]:

                # checks for space
                if (letter != ' '):

                    # counter to keep track of space
                    i = 0

                    # storing morse code of a single character
                    citext += letter

                # in case of space
                else:
                    # if i = 1 that indicates a new character
                    i += 1

                    # if i = 2 that indicates a new word
                    if i == 2:

                        # adding space to separate words
                        decipher += ' '
                    else:

                        # accessing the keys using their values (reverse of encryption)
                        decipher += list(morse_code_dict.keys())[list(morse_code_dict
                                                                      .values()).index(citext)]
                        citext = ''
            return re.sub('(?:[-.] ?){10,5000}', '', message) + ' \nMorse Result: ' +decipher
        else:
            return message
    @staticmethod
    def remove_everything_and_try(message):
        message = re.sub(r' *\([^0-9)]*\) *', '', message)
        message = re.sub(r'[()]*', '', message)
        message = re.sub(r'[^a-fA-Fx0-9\n]+', ' ', message)
        message = re.sub(r' [a-fA-Fx\n]{1,3} ', ' ', message)
        x = re.search(r"0x[a-fA-F0-9]{40}", re.sub(r'[^a-fA-F0-9x]+', '', message))
        if x is None:
            return False
        else:
            print("SUCCESS")
            return x.group(0)

    def glue_operation(self, message: str):
        message = message.replace('first', '')
        message = message.replace('end', '')
        message = message.replace('last', '')
        message = message.replace('second', '')
        message = message.replace('f1rst', '')
        message = message.replace('middle', '')
        x = re.search(r"0x[0-9a-fA-F]+", message)
        if x is None:
            return False
        else:
            first_part = x.group(0)
            message = re.sub(r"0x[0-9a-fA-F]+", '', message)
            x = re.findall(r"[0-9a-fA-F]+", message)
            if len(x) < 1:
                return False
            elif len(x) >= 1:
                if len(x) > 2:
                    for i in range(2, len(x)):
                        shortest = min((word for word in x if word), key=len)
                        x.remove(shortest)
                if len(first_part + x[0]) == 42:
                    return first_part + x[0]
                if len(x) >= 2:
                    possibilities = [first_part + x[0] + x[1], first_part + x[1] + x[0]]
                    print("Trying to glue ")
                    try:
                        code = self.blockchain.web3.eth.get_code(Web3.to_checksum_address(possibilities[0]))
                        if len(code) > 15:
                            print("SUCCESS")
                            print("pos 0", possibilities[0])
                            return possibilities[0]
                        else:
                            print("SUCCESS")
                            print("pos 1", possibilities[1])
                            return possibilities[1]
                    except ValueError:
                        return False
            return False

    @staticmethod
    def word_to_number(message: str) -> str:
        message = message.replace('one', '1')
        message = message.replace('two', '2')
        message = message.replace('three', '3')
        message = message.replace('four', '4')
        message = message.replace('five', '5')
        message = message.replace('f1ve', '5')
        message = message.replace('six', '6')
        message = message.replace('s1x', '6')
        message = message.replace('6ix', '6')
        message = message.replace('seven', '7')
        message = message.replace('7even', '7')
        message = message.replace('eight', '8')
        message = message.replace('e1ght', '8')
        message = message.replace('8ight', '8')
        message = message.replace('nine', '9')
        message = message.replace('n1ne', '9')
        message = message.replace('zero', '0')

        message = message.replace('0️⃣️', '0')
        message = message.replace('1️⃣️️', '1')
        message = message.replace('2️⃣', '2')
        message = message.replace('3️⃣️', '3')
        message = message.replace('4️⃣', '4')
        message = message.replace('5️⃣', '5')
        message = message.replace('6️⃣', '6')
        message = message.replace('7️⃣', '7')
        message = message.replace('8️⃣', '8')
        message = message.replace('9️⃣', '9')
        message = message.replace('🔟', '10')

        return message

    @staticmethod
    def word_to_operator(message: str) -> str:
        message = re.sub(r'([^0])x', r'\1*', message)
        message = message.replace('times', '*')
        message = message.replace('multiply', '*')
        message = message.replace('multiply by', '*')
        message = message.replace('power', '**')
        message = message.replace('power of', '**')
        message = message.replace('power', '**')
        message = message.replace('divide by', '/')
        message = message.replace('divided by', '/')
        message = message.replace('divide', '/')
        message = message.replace('divided', '/')
        message = message.replace('minus', '-')
        message = message.replace('plus', '+')
        message = re.sub(r'root *([0-9-.]+)', r'\1**0.5', message)
        message = re.sub(r'square *([0-9-.]+)', r'\1**2', message)
        message = re.sub(r'cube *([0-9-.]+)', r'\1**3', message)
        message = re.sub(r'√ *([0-9-.]+)', r'\1**0.5', message)
        message = message.replace('cube', '**3')

        return message

    def do_math(self, message: str):
        message = self.word_to_operator(message)
        matches = re.findall(r'[0-9.-]+ *[-+*]{1,2} *[-0-9.]+', message)
        for match in matches:
            try:
                print(match)
                calculation = eval(match)
                message = message.replace(match, str(int(calculation)))
            except SyntaxError:
                pass

        message = re.sub(r' *\([^0-9)]*\) *', '', message)
        message = message.replace('*', 'x')
        message = re.sub(r'[^a-fA-Fx0-9\n]+', '', message)
        x = re.search(r"0x[a-fA-F0-9]{40}", message)
        if x is not None:
            print("SUCCESS")
            return x.group(0)
        else:
            return False
