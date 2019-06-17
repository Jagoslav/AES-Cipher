"""
Created on Sun may 6 14:07:52 2018

@author: Jakub Grzeszczak
"""


from tkinter import messagebox
from tkinter import filedialog
from tkinter import *
import constants as cons
import copy

string_blocks = []
input_blocks = []  # Blocks to encode/decode
RCon = []  # Round Constant Values
keys = []  # Round Keys
rounds = 11  # Number of rounds
current_round = 0  # current operation id
current_block = 0  # current block id
round_operations = {}  # dictionary of operations performed on current round
operation = None  # encode/decodee operation marker for step by step display
block_size = 16

def create_rcon():
    global RCon
    del RCon[:]
    RCon.append([0x01, 0x00, 0x00, 0x00])
    for col in range(1, rounds + 1):
        RCon.append([2 * col, 0x00, 0x00, 0x00])


def get_column(column_index, table):
    column = []
    for row in table:
        column.append(row[column_index])
    return column


def rot_word(column):
    column.append(column.pop(0))
    return column


def add_round_key(state_tab, key):
    new_table = []
    for row in range(0, len(state_tab)):
        new_table.append([])
    for col in range(0, len(state_tab[0])):
        first_column = get_column(col, state_tab)
        second_column = get_column(col, key)
        for row in range(0, len(state_tab)):
            new_table[row].append(first_column[row] ^ second_column[row])
    return new_table


def key_schedule(key_list):
    global RCon
    for keyIter in range(0, rounds + 1):
        new_key = []
        new_column = []
        used_column = 0
        # First column
        column = get_column(len(key_list[keyIter][0]) - 1, key_list[keyIter])
        column = [cons.SBox[x] for x in rot_word(column)]
        next_column = get_column(used_column, key_list[keyIter])
        rcon_column = RCon.pop(0)
        for row in range(0, len(key_list[keyIter])):
            new_key.append([])
            new_value = next_column[row] ^ column[row] ^ rcon_column[row]
            new_column.append(new_value)
            new_key[row].append(new_value)
        # All the other columns
        for col in range(1, len(key_list[keyIter][0])):
            used_column += 1
            next_column = get_column(used_column, key_list[keyIter])
            for row in range(0, len(key_list[keyIter])):
                new_value = next_column[row] ^ new_column[0]
                new_column.append(new_value)
                new_column.pop(0)
                new_key[row].append(new_value)
        key_list.append(new_key)
    create_rcon()
    return key_list


def sub_bytes(to_sub, sub_table):
    return [[sub_table[x] for x in row] for row in to_sub]


def shift_rows(shift):
    shift[1][0], shift[1][1], shift[1][2], shift[1][3] = shift[1][1], shift[1][2], shift[1][3], shift[1][0]
    shift[2][0], shift[2][1], shift[2][2], shift[2][3] = shift[2][2], shift[2][3], shift[2][0], shift[2][1]
    shift[3][0], shift[3][1], shift[3][2], shift[3][3] = shift[3][3], shift[3][0], shift[3][1], shift[3][2]
    return shift


def inv_shift_rows(shift):
    shift[1][0], shift[1][1], shift[1][2], shift[1][3] = shift[1][3], shift[1][0], shift[1][1], shift[1][2]
    shift[2][0], shift[2][1], shift[2][2], shift[2][3] = shift[2][2], shift[2][3], shift[2][0], shift[2][1]
    shift[3][0], shift[3][1], shift[3][2], shift[3][3] = shift[3][1], shift[3][2], shift[3][3], shift[3][0]
    return shift


def mix_columns(to_mix):
    t00 = cons.MulBy2[to_mix[0][0]] ^ cons.MulBy3[to_mix[1][0]] ^ to_mix[2][0] ^ to_mix[3][0]
    t10 = to_mix[0][0] ^ cons.MulBy2[to_mix[1][0]] ^ cons.MulBy3[to_mix[2][0]] ^ to_mix[3][0]
    t20 = to_mix[0][0] ^ to_mix[1][0] ^ cons.MulBy2[to_mix[2][0]] ^ cons.MulBy3[to_mix[3][0]]
    t30 = cons.MulBy3[to_mix[0][0]] ^ to_mix[1][0] ^ to_mix[2][0] ^ cons.MulBy2[to_mix[3][0]]

    t01 = cons.MulBy2[to_mix[0][1]] ^ cons.MulBy3[to_mix[1][1]] ^ to_mix[2][1] ^ to_mix[3][1]
    t11 = to_mix[0][1] ^ cons.MulBy2[to_mix[1][1]] ^ cons.MulBy3[to_mix[2][1]] ^ to_mix[3][1]
    t21 = to_mix[0][1] ^ to_mix[1][1] ^ cons.MulBy2[to_mix[2][1]] ^ cons.MulBy3[to_mix[3][1]]
    t31 = cons.MulBy3[to_mix[0][1]] ^ to_mix[1][1] ^ to_mix[2][1] ^ cons.MulBy2[to_mix[3][1]]

    t02 = cons.MulBy2[to_mix[0][2]] ^ cons.MulBy3[to_mix[1][2]] ^ to_mix[2][2] ^ to_mix[3][2]
    t12 = to_mix[0][2] ^ cons.MulBy2[to_mix[1][2]] ^ cons.MulBy3[to_mix[2][2]] ^ to_mix[3][2]
    t22 = to_mix[0][2] ^ to_mix[1][2] ^ cons.MulBy2[to_mix[2][2]] ^ cons.MulBy3[to_mix[3][2]]
    t32 = cons.MulBy3[to_mix[0][2]] ^ to_mix[1][2] ^ to_mix[2][2] ^ cons.MulBy2[to_mix[3][2]]

    t03 = cons.MulBy2[to_mix[0][3]] ^ cons.MulBy3[to_mix[1][3]] ^ to_mix[2][3] ^ to_mix[3][3]
    t13 = to_mix[0][3] ^ cons.MulBy2[to_mix[1][3]] ^ cons.MulBy3[to_mix[2][3]] ^ to_mix[3][3]
    t23 = to_mix[0][3] ^ to_mix[1][3] ^ cons.MulBy2[to_mix[2][3]] ^ cons.MulBy3[to_mix[3][3]]
    t33 = cons.MulBy3[to_mix[0][3]] ^ to_mix[1][3] ^ to_mix[2][3] ^ cons.MulBy2[to_mix[3][3]]
    return [[t00, t01, t02, t03],
            [t10, t11, t12, t13],
            [t20, t21, t22, t23],
            [t30, t31, t32, t33]]


def inv_mix_columns(mix):
    t00 = cons.MulBy14[mix[0][0]] ^ cons.MulBy11[mix[1][0]] ^ cons.MulBy13[mix[2][0]] ^ cons.MulBy9[mix[3][0]]
    t10 = cons.MulBy9[mix[0][0]] ^ cons.MulBy14[mix[1][0]] ^ cons.MulBy11[mix[2][0]] ^ cons.MulBy13[mix[3][0]]
    t20 = cons.MulBy13[mix[0][0]] ^ cons.MulBy9[mix[1][0]] ^ cons.MulBy14[mix[2][0]] ^ cons.MulBy11[mix[3][0]]
    t30 = cons.MulBy11[mix[0][0]] ^ cons.MulBy13[mix[1][0]] ^ cons.MulBy9[mix[2][0]] ^ cons.MulBy14[mix[3][0]]

    t01 = cons.MulBy14[mix[0][1]] ^ cons.MulBy11[mix[1][1]] ^ cons.MulBy13[mix[2][1]] ^ cons.MulBy9[mix[3][1]]
    t11 = cons.MulBy9[mix[0][1]] ^ cons.MulBy14[mix[1][1]] ^ cons.MulBy11[mix[2][1]] ^ cons.MulBy13[mix[3][1]]
    t21 = cons.MulBy13[mix[0][1]] ^ cons.MulBy9[mix[1][1]] ^ cons.MulBy14[mix[2][1]] ^ cons.MulBy11[mix[3][1]]
    t31 = cons.MulBy11[mix[0][1]] ^ cons.MulBy13[mix[1][1]] ^ cons.MulBy9[mix[2][1]] ^ cons.MulBy14[mix[3][1]]

    t02 = cons.MulBy14[mix[0][2]] ^ cons.MulBy11[mix[1][2]] ^ cons.MulBy13[mix[2][2]] ^ cons.MulBy9[mix[3][2]]
    t12 = cons.MulBy9[mix[0][2]] ^ cons.MulBy14[mix[1][2]] ^ cons.MulBy11[mix[2][2]] ^ cons.MulBy13[mix[3][2]]
    t22 = cons.MulBy13[mix[0][2]] ^ cons.MulBy9[mix[1][2]] ^ cons.MulBy14[mix[2][2]] ^ cons.MulBy11[mix[3][2]]
    t32 = cons.MulBy11[mix[0][2]] ^ cons.MulBy13[mix[1][2]] ^ cons.MulBy9[mix[2][2]] ^ cons.MulBy14[mix[3][2]]

    t03 = cons.MulBy14[mix[0][3]] ^ cons.MulBy11[mix[1][3]] ^ cons.MulBy13[mix[2][3]] ^ cons.MulBy9[mix[3][3]]
    t13 = cons.MulBy9[mix[0][3]] ^ cons.MulBy14[mix[1][3]] ^ cons.MulBy11[mix[2][3]] ^ cons.MulBy13[mix[3][3]]
    t23 = cons.MulBy13[mix[0][3]] ^ cons.MulBy9[mix[1][3]] ^ cons.MulBy14[mix[2][3]] ^ cons.MulBy11[mix[3][3]]
    t33 = cons.MulBy11[mix[0][3]] ^ cons.MulBy13[mix[1][3]] ^ cons.MulBy9[mix[2][3]] ^ cons.MulBy14[mix[3][3]]
    return [[t00, t01, t02, t03],
            [t10, t11, t12, t13],
            [t20, t21, t22, t23],
            [t30, t31, t32, t33]]


def prepare_string(input_string):
    input_string = input_string.replace("ą", "a")
    input_string = input_string.replace("Ą", "A")
    input_string = input_string.replace("ć", "c")
    input_string = input_string.replace("Ć", "C")
    input_string = input_string.replace("ę", "e")
    input_string = input_string.replace("Ę", "E")
    input_string = input_string.replace("ł", "l")
    input_string = input_string.replace("Ł", "L")
    input_string = input_string.replace("ó", "o")
    input_string = input_string.replace("Ó", "O")
    input_string = input_string.replace("ś", "s")
    input_string = input_string.replace("Ś", "S")
    input_string = input_string.replace("ż", "z")
    input_string = input_string.replace("Ż", "Z")
    input_string = input_string.replace("ź", "z")
    input_string = input_string.replace("Ź", "Z")
    return input_string


def encrypt(curr_operation):
    if not message_input_scrolledtext.get('0.0', tk.END)[:-1]:
        return
    global keys
    global current_block
    global input_blocks
    global string_blocks
    global blockVar
    global block_text_input_label
    global operation
    global round_operations
    user_input = prepare_string(message_input_scrolledtext.get('0.0', tk.END)[:-1])
    user_key = split_into_blocks(prepare_string(key_entry.get()))[0]
    del keys[:]
    del input_blocks[:]
    create_rcon()
    string_blocks = split_into_blocks(user_input)
    input_blocks = convert_to_integers(user_input)
    keys.append(convert_to_integers(user_key)[0])
    keys = key_schedule(keys)
    block_text_input_entry.config(state='normal')
    block_text_input_entry.delete(0, END)
    block_text_input_entry.insert(0, string_blocks[0])
    block_text_input_entry.config(state='readonly')
    message_output_scrolledtext.config(state='normal')
    message_output_scrolledtext.delete('0.0', tk.END)
    message_output_scrolledtext.config(state='disabled')
    blockVar.set(str(current_block + 1) + '/' + str(len(input_blocks)))
    block_first_button.config(state="normal")
    block_previous_button.config(state="normal")
    block_next_button.config(state="normal")
    block_last_button.config(state="normal")
    round_first_button.config(state="normal")
    round_previous_button.config(state="normal")
    roundVar.set(str(current_round + 1) + '/11')
    round_next_button.config(state="normal")
    round_last_button.config(state="normal")
    block_text_input_label.config(text="to " + curr_operation + ":")
    operation = curr_operation
    if curr_operation == "encode":
        encode()
        round_operations = get_encode_status()
    elif curr_operation == "decode":
        decode()
        round_operations = get_decode_status()
    change_round("0")


def encode():
    global keys
    global input_blocks
    # Encoding process
    for input_block in input_blocks:
        input_block = add_round_key(input_block, keys[0])
        for r_id in range(1, rounds - 1):
            input_block = sub_bytes(input_block, cons.SBox)
            input_block = shift_rows(input_block)
            input_block = mix_columns(input_block)
            input_block = add_round_key(input_block, keys[r_id])
        input_block = sub_bytes(input_block, cons.SBox)
        input_block = shift_rows(input_block)
        input_block = add_round_key(input_block, keys[rounds - 1])
        message_output_scrolledtext.config(state='normal')
        message_output_scrolledtext.insert(tk.END, convert_to_string(input_block))
        message_output_scrolledtext.config(state='disabled')


def get_encode_status():
    global current_block
    global input_blocks
    global current_round
    global keys
    dict_to_return = {}
    block_to_encode = input_blocks[current_block]
    if current_round == 0:
        original = copy.deepcopy(block_to_encode)
        after_add_round_key = copy.deepcopy(add_round_key(block_to_encode, keys[0]))
        dict_to_return["Add round key"] = (original, after_add_round_key)
        return dict_to_return
    else:
        block_to_encode = add_round_key(block_to_encode, keys[0])
    for r_id in range(1, rounds - 1):
        if current_round == r_id:
            original = copy.deepcopy(block_to_encode)
            block_to_encode = sub_bytes(block_to_encode, cons.SBox)
            after_sub_bytes = copy.deepcopy(block_to_encode)
            block_to_encode = shift_rows(block_to_encode)
            after_shift_rows = copy.deepcopy(block_to_encode)
            block_to_encode = mix_columns(block_to_encode)
            after_mix_columns = copy.deepcopy(block_to_encode)
            block_to_encode = add_round_key(block_to_encode, keys[r_id])
            after_add_round_key = copy.deepcopy(block_to_encode)
            dict_to_return["Substitute bytes"] = (original, after_sub_bytes)
            dict_to_return["Shift rows"] = (after_sub_bytes, after_shift_rows)
            dict_to_return["Mix columns"] = (after_shift_rows, after_mix_columns)
            dict_to_return["Add round key"] = (after_mix_columns, after_add_round_key)
            return dict_to_return
        else:
            block_to_encode = sub_bytes(block_to_encode, cons.SBox)
            block_to_encode = shift_rows(block_to_encode)
            block_to_encode = mix_columns(block_to_encode)
            block_to_encode = add_round_key(block_to_encode, keys[r_id])
    original = copy.deepcopy(block_to_encode)
    block_to_encode = sub_bytes(block_to_encode, cons.SBox)
    after_sub_bytes = copy.deepcopy(block_to_encode)
    block_to_encode = shift_rows(block_to_encode)
    after_shift_rows = copy.deepcopy(block_to_encode)
    block_to_encode = add_round_key(block_to_encode, keys[rounds - 1])
    after_add_round_key = copy.deepcopy(block_to_encode)
    dict_to_return["Substitute bytes"] = (original, after_sub_bytes)
    dict_to_return["Shift rows"] = (after_sub_bytes, after_shift_rows)
    dict_to_return["Add round key"] = (after_shift_rows, after_add_round_key)
    return dict_to_return


def decode():
    global keys
    global input_blocks
    # Decoding process
    for input_block in input_blocks:
        input_block = add_round_key(input_block, keys[rounds - 1])
        input_block = inv_shift_rows(input_block)
        input_block = sub_bytes(input_block, cons.InvSBox)
        for r_id in range(rounds - 2, 0, - 1):
            input_block = add_round_key(input_block, keys[r_id])
            input_block = inv_mix_columns(input_block)
            input_block = inv_shift_rows(input_block)
            input_block = sub_bytes(input_block, cons.InvSBox)
        input_block = add_round_key(input_block, keys[0])
        message_output_scrolledtext.config(state='normal')
        message_output_scrolledtext.insert(tk.END, convert_to_string(input_block))
        message_output_scrolledtext.config(state='disabled')


def get_decode_status():
    global current_block
    global input_blocks
    global current_round
    global keys
    dict_to_return = {}
    block_to_encode = input_blocks[current_block]
    if current_round == 0:
        original = copy.deepcopy(block_to_encode)
        block_to_encode = add_round_key(block_to_encode, keys[rounds - 1])
        after_add_round_key = copy.deepcopy(block_to_encode)
        block_to_encode = inv_shift_rows(block_to_encode)
        after_shift_rows = copy.deepcopy(block_to_encode)
        block_to_encode = sub_bytes(block_to_encode, cons.InvSBox)
        after_sub_bytes = copy.deepcopy(block_to_encode)
        dict_to_return["Add round key"] = (original, after_add_round_key)
        dict_to_return["Shift rows"] = (after_add_round_key, after_shift_rows)
        dict_to_return["Substitute bytes"] = (after_shift_rows, after_sub_bytes)
        return dict_to_return
    else:
        block_to_encode = add_round_key(block_to_encode, keys[rounds - 1])
        block_to_encode = inv_shift_rows(block_to_encode)
        block_to_encode = sub_bytes(block_to_encode, cons.InvSBox)
    for r_id in range(rounds - 2, 0, -1):
        if current_round == rounds - 1 - r_id:
            original = copy.deepcopy(block_to_encode)
            block_to_encode = add_round_key(block_to_encode, keys[r_id])
            after_add_round_key = copy.deepcopy(block_to_encode)
            block_to_encode = inv_mix_columns(block_to_encode)
            after_mix_columns = copy.deepcopy(block_to_encode)
            block_to_encode = inv_shift_rows(block_to_encode)
            after_shift_rows = copy.deepcopy(block_to_encode)
            block_to_encode = sub_bytes(block_to_encode, cons.InvSBox)
            after_sub_bytes = copy.deepcopy(block_to_encode)
            dict_to_return["Add round key"] = (original, after_add_round_key)
            dict_to_return["Mix columns"] = (after_add_round_key, after_mix_columns)
            dict_to_return["Shift rows"] = (after_mix_columns, after_shift_rows)
            dict_to_return["Substitute bytes"] = (after_shift_rows, after_sub_bytes)
            return dict_to_return
        else:
            block_to_encode = add_round_key(block_to_encode, keys[r_id])
            block_to_encode = inv_mix_columns(block_to_encode)
            block_to_encode = inv_shift_rows(block_to_encode)
            block_to_encode = sub_bytes(block_to_encode, cons.InvSBox)
    original = copy.deepcopy(block_to_encode)
    block_to_encode = add_round_key(block_to_encode, keys[0])
    dict_to_return["Add round key"] = (original, block_to_encode)
    return dict_to_return


def copy_to_input():
    if not message_output_scrolledtext.get("0.0", tk.END)[:-1]:
        return
    message_input_scrolledtext.delete("0.0", tk.END)
    message_input_scrolledtext.insert(tk.END, message_output_scrolledtext.get("0.0", tk.END)[:-1])
    message_output_scrolledtext.config(state="normal")
    message_output_scrolledtext.delete("0.0", tk.END)
    message_output_scrolledtext.config(state="disabled")


def save_output():
    if not message_output_scrolledtext.get("0.0", tk.END)[:-1]:
        messagebox.showerror("Error",
                             "Nothing to save")
        return
    filename = filedialog.asksaveasfilename(initialdir="/",
                                            title="Save file",
                                            filetypes=(("AES128 Encrypted Files", "*.AES"),
                                                       ("All files", "*.*")))
    if filename:
        try:
            if filename[-4:] == ".AES":
                file = open(filename, 'w', encoding="utf-8")
            else:
                file = open(filename + '.AES', 'w', encoding="utf-8")
            file.write(message_output_scrolledtext.get('0.0', tk.END)[:-1])
            messagebox.showinfo("Success",
                                "File Saved")
            file.close()
        except IOError:
            messagebox.showerror("Error",
                                 "Failed to save a file")


def load_input():
    filename = filedialog.askopenfilename(title="Load file",
                                          filetypes=(("AES128 Encrypted Files", "*.AES"),
                                                     ("All files", "*.*")))
    if filename:
        try:
            file = open(filename, encoding="utf-8")
            text = file.readlines()
            file.close()
            message_input_scrolledtext.delete('0.0', tk.END)
            message_input_scrolledtext.insert(tk.END, "".join(text))
            message_output_scrolledtext.config(state='normal')
            message_output_scrolledtext.delete('0.0', tk.END)
            message_output_scrolledtext.config(state='disabled')
        except IOError:
            messagebox.showerror("Error",
                                 "Loading failed")


def change_block(shift):
    global string_blocks
    global current_block
    global blockVar
    global current_round
    temp_block_id = current_block
    if shift == '0':
        current_block = 0
    elif shift == '-':
        current_block = max(0, current_block - 1)
    elif shift == '+':
        current_block = min(current_block + 1, len(input_blocks) - 1)
    else:
        current_block = len(input_blocks) - 1
    if temp_block_id != current_block:
        change_round(0)
    block_text_input_entry.config(state='normal')
    block_text_input_entry.delete(0, END)
    block_text_input_entry.insert(0, string_blocks[current_block])
    block_text_input_entry.config(state='readonly')
    blockVar.set(str(current_block + 1) + '/' + str(len(input_blocks)))


def change_round(shift):
    global current_round
    global rounds
    global operation
    global round_operations
    global step_displayed_var
    temp_round_id = current_round
    if shift == '0':
        current_round = 0
    elif shift == '-':
        current_round = max(0, current_round - 1)
    elif shift == '+':
        current_round = min(current_round + 1, rounds - 1)
    else:
        current_round = rounds - 1
    if temp_round_id != current_round:
        if operation == "encode":
            round_operations = get_encode_status()
        elif operation == "decode":
            round_operations = get_decode_status()
    roundVar.set(str(current_round + 1) + '/' + str(rounds))
    if "Substitute bytes" in round_operations:
        subBytes_radiobutton.config(state="normal")
    else:
        subBytes_radiobutton.config(state="disabled")
    if "Shift rows" in round_operations:
        shiftRows_radiobutton.config(state="normal")
    else:
        shiftRows_radiobutton.config(state="disabled")
    if "Mix columns" in round_operations:
        mixColumns_radiobutton.config(state="normal")
    else:
        mixColumns_radiobutton.config(state="disabled")
    if "Add round key" in round_operations:
        addRoundKey_radiobutton.config(state="normal")
    else:
        addRoundKey_radiobutton.config(state="disabled")
    step_displayed_var.set(list(round_operations.keys())[0])
    display_step()
    if operation == "encode":
        subBytes_radiobutton.place(x=645, y=120, width=220, height=30)
        shiftRows_radiobutton.place(x=645, y=150, width=220, height=30)
        mixColumns_radiobutton.place(x=645, y=180, width=220, height=30)
        addRoundKey_radiobutton.place(x=645, y=210, width=220, height=30)
    else:
        subBytes_radiobutton.place(x=645, y=210, width=220, height=30)
        shiftRows_radiobutton.place(x=645, y=180, width=220, height=30)
        mixColumns_radiobutton.place(x=645, y=150, width=220, height=30)
        addRoundKey_radiobutton.place(x=645, y=120, width=220, height=30)


def display_step():
    global labels_after_matrix
    global labels_before_matrix
    global round_operations
    global step_displayed_var
    global labels_round_key
    global keys
    global current_round
    if step_displayed_var.get() == "temp":
        for field_id in labels_before_matrix:
            labels_before_matrix[field_id]["text"] = hex(0)
            labels_after_matrix[field_id]["text"] = hex(0)
            labels_round_key[field_id]["text"] = hex(0)
    else:
        values = round_operations[step_displayed_var.get()]
        for row_id in range(len(values[0])):
            for column_id in range(len(values[0][row_id])):
                labels_before_matrix[str(row_id) + str(column_id)]["text"] = hex(values[0][row_id][column_id])
                labels_after_matrix[str(row_id) + str(column_id)]["text"] = hex(values[1][row_id][column_id])
                labels_round_key[str(row_id) + str(column_id)]["text"] = hex(keys[current_round][row_id][column_id])


def convert_to_integers(string):
    block_list = []
    string_list = split_into_blocks(string)
    for stringIndex in range(0, len(string_list)):
        block = []
        row = []
        for character in string_list[stringIndex]:
            row.append(ord(character))
            if len(row) == 4:
                block.append(row)
                row = []
        block_list.append(block)
    return block_list


def convert_to_string(integers_tab):
    new_string = ""
    for row in integers_tab:
        for c in row:
            new_string += chr(c)
    return new_string


def split_into_blocks(string):
    temp_list = []
    while len(string) > block_size:
        sub_str, string = string[0:block_size], string[block_size:]
        temp_list.append(sub_str)
    while len(string) < block_size:
        string += '#'
    temp_list.append(string)
    return temp_list


if __name__ == "__main__":
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText

    window = tk.Tk()
    window.title("AES 128")
    window.resizable(width=False, height=False)
    window.geometry("%dx%d+%d+%d" % (870, 460,
                                     window.winfo_screenwidth() / 2 - 435,
                                     window.winfo_screenheight() / 2 - 230))


    def limit_length(after_change, limit):
        return len(after_change) <= int(limit)


    reg = window.register(limit_length)

    # Top half
    label_before = Label(window, text="Before:", font=(None, 14), borderwidth=6, relief="groove")
    label_before.place(x=5, y=5, width=180, height=35)
    label_after = Label(window, text="After:", font=(None, 14), borderwidth=6, relief="groove")
    label_after.place(x=220, y=5, width=180, height=35)
    label_after = Label(window, text="Round key:", font=(None, 14), borderwidth=6, relief="groove")
    label_after.place(x=440, y=5, width=180, height=35)

    labels_before_matrix = {}
    labels_after_matrix = {}
    labels_round_key = {}
    for i in range(0, 4):
        for j in range(0, 4):
            labels_before_matrix[str(i) + str(j)] = Label(window, text=hex(0), borderwidth=6, relief="groove")
            labels_before_matrix[str(i) + str(j)].place(x=(5+j*45), y=(45+i*50), width=45, height=45)
            labels_after_matrix[str(i) + str(j)] = Label(window, text=hex(0), borderwidth=6, relief="groove")
            labels_after_matrix[str(i) + str(j)].place(x=(220+j*45), y=(45+i*50), width=45, height=45)
            labels_round_key[str(i) + str(j)] = Label(window, text=hex(0), borderwidth=6, relief="groove")
            labels_round_key[str(i) + str(j)].place(x=(440+j*45), y=(45+i*50), width=45, height=45)

    blockVar = StringVar()
    blockVar.set(str(current_block) + '/' + str(len(input_blocks)))
    roundVar = StringVar()
    roundVar.set(str(current_round) + '/' + str(rounds))

    block_number_label = Label(window, text="Blocks: ")
    block_number_label.place(x=650, y=5, width=40, height=30)
    block_first_button = tk.Button(window, text="<<", state="disabled", command=lambda: change_block("0"))
    block_first_button.place(x=690, y=5, width=25, height=30)
    block_previous_button = tk.Button(window, text="<", state="disabled", command=lambda: change_block("-"))
    block_previous_button.place(x=720, y=5, width=25, height=30)
    block_number_label = Label(window, textvariable=blockVar)
    block_number_label.place(x=750, y=5, width=55, height=30)
    block_next_button = tk.Button(window, text=">", state="disabled", command=lambda: change_block("+"))
    block_next_button.place(x=810, y=5, width=25, height=30)
    block_last_button = tk.Button(window, text=">>", state="disabled", command=lambda: change_block("end"))
    block_last_button.place(x=840, y=5, width=25, height=30)

    round_number_label = Label(window, text="Rounds: ")
    round_number_label.place(x=644, y=40, width=45, height=30)
    round_first_button = tk.Button(window, text="<<", state='disabled', command=lambda: change_round("0"))
    round_first_button.place(x=690, y=40, width=25, height=30)
    round_previous_button = tk.Button(window, text="<", state='disabled', command=lambda: change_round("-"))
    round_previous_button.place(x=720, y=40, width=25, height=30)
    round_number_label = Label(window, textvariable=roundVar)
    round_number_label.place(x=750, y=40, width=55, height=30)
    round_next_button = tk.Button(window, text=">", state='disabled', command=lambda: change_round("+"))
    round_next_button.place(x=810, y=40, width=25, height=30)
    round_last_button = tk.Button(window, text=">>", state='disabled', command=lambda: change_round("end"))
    round_last_button.place(x=840, y=40, width=25, height=30)

    block_text_input_label = tk.Label(window, text="to encode:")
    block_text_input_label.place(x=642, y=75, width=60, height=15)

    block_text_input_entry = tk.Entry(window)
    block_text_input_entry.config(state='readonly')
    block_text_input_entry.place(x=705, y=75, width=160, height=20)

    operations_label = Label(window, text="Operations in this round: ")
    operations_label.place(x=695, y=95, width=150, height=30)

    step_displayed_var = StringVar()
    subBytes_radiobutton = tk.Radiobutton(window, text="Substitute Bytes", state="disabled", indicatoron=0,
                                          variable=step_displayed_var, value="Substitute bytes", command=display_step)
    subBytes_radiobutton.place(x=645, y=120, width=220, height=30)
    shiftRows_radiobutton = tk.Radiobutton(window, text="Shift rows", state="disabled", indicatoron=0,
                                           variable=step_displayed_var, value="Shift rows", command=display_step)
    shiftRows_radiobutton.place(x=645, y=150, width=220, height=30)
    mixColumns_radiobutton = tk.Radiobutton(window, text="Mix columns", state="disabled", indicatoron=0,
                                            variable=step_displayed_var, value="Mix columns", command=display_step)
    mixColumns_radiobutton.place(x=645, y=180, width=220, height=30)
    addRoundKey_radiobutton = tk.Radiobutton(window, text="Add round key", state="disabled", indicatoron=0,
                                             variable=step_displayed_var, value="Add round key", command=display_step)
    addRoundKey_radiobutton.place(x=645, y=210, width=220, height=30)
    #  middle bar
    bar = tk.Label(window, borderwidth=4, relief="sunken")
    bar.place(x=0, y=245, width=870, height=10)
    bar = tk.Label(window, borderwidth=4, relief="sunken")
    bar.place(x=625, y=0, width=10, height=466)
    # Bottom half
    message_input_label = tk.Label(window, text="Input Message:")
    message_input_label.place(x=5, y=260, width=100, height=15)
    message_input_scrolledtext = ScrolledText(window)
    message_input_scrolledtext.place(x=5, y=280, width=610, height=75)
    message_output_label = tk.Label(window, text="Output Message:")
    message_output_label.place(x=5, y=360, width=100, height=15)
    message_output_scrolledtext = ScrolledText(window, state='disabled')
    message_output_scrolledtext.place(x=5, y=380, width=610, height=75)

    key_label = tk.Label(window, text="key: ")
    key_label.place(x=675, y=260, width=30, height=20)

    key_entry = tk.Entry(window)
    key_entry.config(validate="key", validatecommand=(reg, '%P', block_size))
    key_entry.place(x=705, y=260, width=160, height=20)

    encode_button = tk.Button(window, text="Encode", command=lambda: encrypt("encode"))
    encode_button.place(x=645, y=285, width=220, height=30)

    decode_button = tk.Button(window, text="Decode", command=lambda: encrypt("decode"))
    decode_button.place(x=645, y=320, width=220, height=30)

    copy_to_input_button = tk.Button(window, text="Copy Output", command=copy_to_input)
    copy_to_input_button.place(x=645, y=355, width=220, height=30)

    save_output_button = tk.Button(window, text="Save Message", command=save_output)
    save_output_button.place(x=645, y=390, width=220, height=30)

    load_input_button = tk.Button(window, text="Load Message", command=load_input)
    load_input_button.place(x=645, y=425, width=220, height=30)
    window.mainloop()
