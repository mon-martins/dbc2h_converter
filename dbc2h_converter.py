import cantools
from datetime import datetime

import sys
import os

if(len(sys.argv) < 3): raise Exception("missing parameter, usage: directory_of_dbc name_of_dbc_file system_name")

# dbc path
source_path = sys.argv[1]
# name of your node
system_name = sys.argv[2]

dbc_files = []
dbc_files += [each for each in os.listdir(source_path) if each.endswith('.dbc')]

for file in dbc_files:

    file = str(file)
    source_file = file.removesuffix('.dbc')

    output_file_name = source_file

    dbc_inst = cantools.db.load_file(source_path+"/"+source_file+".dbc")

    header = open(output_file_name + ".h", "w", encoding="utf-8")

    header.write( "/************************************************************/\n")
    header.write( "// Automatically generated C header file from CAN DBC file\n")
    header.write(f"// Source file name: {source_file}.dbc\n")
    header.write(f"// Date created: {datetime.now().strftime('%Y-%m-%d')}\n")
    header.write( "/************************************************************/\n")
    header.write( "\n")
    header.write( "\n")

    header.write(f"#ifndef _{source_file.upper()}_DBC_H_")
    header.write("\n")
    header.write(f"#define _{source_file.upper()}_DBC_H_")

    header.write( "\n")
    header.write( "\n")
    header.write( "/************************************************************/\n")
    header.write( "//====================Messages Proprieties====================\n")
    header.write( "/************************************************************/\n")
    header.write( "\n")

    there_is_msg_ext = 0
    mask_ones_ext = 0x00000000
    mask_zeros_ext = 0x00000000

    for message in dbc_inst.messages:
        if message.is_extended_frame:
            there_is_msg_ext = 1
            if system_name in message.receivers:
                mask_ones_ext  |= message.frame_id
                mask_zeros_ext |= ~message.frame_id

    mask_ones_ext  &= 0x01FFFFFF
    mask_zeros_ext &= 0x01FFFFFF

    receive_id_ext   = f"0x{mask_ones_ext & 0x1FFFFFFF:08x}"
    receive_mask_ext = f"0x{(~(mask_ones_ext^mask_zeros_ext)&0x1FFFFFFF):08x}"

    there_is_msg_std = 0
    mask_ones_std = 0x0000
    mask_zeros_std = 0x0000

    for message in dbc_inst.messages:
        if not message.is_extended_frame:
            there_is_msg_std = 1
            if system_name in message.receivers:
                mask_ones_std  |= message.frame_id
                mask_zeros_std |= ~message.frame_id

    mask_ones_std  &= 0x07FF
    mask_zeros_std &= 0x07FF

    receive_id_std   = f"0x{mask_ones_std & 0x07FF:04x}"
    receive_mask_std = f"0x{(~(mask_ones_std^mask_zeros_std)&0x07FF):04x}"

    header.write( "\n")
    header.write( "\n")
    if there_is_msg_ext:
        header.write( f"#define {source_file.upper()}_CAN_MSG_RECEIVE_ID_EXT {receive_id_ext}\n")
        header.write( f"#define {source_file.upper()}_CAN_MSG_RECEIVE_MASK_EXT {receive_mask_ext}\n")
    if there_is_msg_std:
        header.write( f"#define {source_file.upper()}_CAN_MSG_RECEIVE_ID_STD {receive_id_std}\n")
        header.write( f"#define {source_file.upper()}_CAN_MSG_RECEIVE_MASK_STD {receive_mask_std}\n")
    header.write( "\n")
    header.write( "\n")

    for message in dbc_inst.messages:
        header.write( "\n")
        header.write( "/************************************************************/\n")
        header.write(f"// Message: {message.name}\n")
        header.write( "/************************************************************/\n")
        header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name} {source_file.upper()}_CAN_MSG_{message.name}\n")
        header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_FRAME_ID {hex(message.frame_id)}\n")
        header.write( "\n")
        header.write( "typedef struct{\n")
        
        bit_start = 0
        for signal in message.signals:
            assert bit_start <= signal.start , "Overlaid signals"
            padding_bits = signal.start - bit_start
            if padding_bits>0:
                header.write(f"    // padding {bit_start}-{bit_start+padding_bits-1}\n")
                header.write(f"    uint64_t padding_{bit_start}:{padding_bits};\n")
            bit_start = bit_start+padding_bits

            if signal.is_float:
                if signal.length == 32:
                    sig_type = 'float32_t'
                    if not(bit_start == 0 or bit_start == 32):
                        raise Exception("the float32 value must be init on bit 0 or bit 32")
                elif signal.length ==64:
                    sig_type = 'float64_t'
                    if not(bit_start == 0):
                        raise Exception("the float64 value must be init on bit 0")
                else:
                    raise Exception("A float pointer must be 32bit or 64bit sized")
            elif signal.is_signed:
                sig_type = 'int64_t'
            else:
                sig_type = 'uint64_t'
            
            header.write(f"    // CAN_SIG_{signal.name} , bits {bit_start}-{bit_start+signal.length-1}\n")
            header.write(f"    {sig_type} CAN_SIG_{signal.name}")
            if(not signal.is_float):
                header.write(f":{signal.length}")
            header.write( ";\n")
            bit_start = bit_start + signal.length
        if bit_start<64:
            header.write(f"    // undef {bit_start}-{63} \n")
            header.write(f"    uint64_t undef:{64-bit_start};\n")
        header.write( "}")
        header.write(f"{source_file.upper()}_CAN_MSG_{message.name}_t;\n")

        header.write("\n")
        for signal in message.signals:
            header.write(f"// Signal: {signal.name}\n")
            header.write(f"#define CAN_SIG_{signal.name} CAN_SIG_{signal.name}\n")
            if signal.is_signed:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE int64_t\n")
            else:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE int64_t\n")
            
            if signal.scale != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_SCALE {signal.scale}\n")
            else:
                header.write( "#error \"the scale must be a number\"\n")
                raise Exception(f"the scale of {signal.name} in {message.name} must be a number")
            
            if signal.offset != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_OFFSET {signal.offset}\n")
            else:
                header.write( "#error \"the offset must be a number\"\n")
                raise Exception(f"the offset of {signal.name} in {message.name} must be a number")
            
            if signal.minimum != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_MINIMUM {signal.minimum}\n")
            else:
                header.write( "#error \"the minimum must be a number\"\n")
                raise Exception(f"the minimum of {signal.name} in {message.name} must be a number")
            
            if signal.maximum != None and signal.maximum>signal.minimum:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_MAXIMUM {signal.maximum}\n")
            else:
                header.write( "#error \"the maximum must be a number\"\n")
                raise Exception(f"the maximum of {signal.name} in {message.name} must be a number and larger than minimum")

            total_size = ( (2**(signal.length)-1) )
            max_encoded = (signal.maximum - signal.offset)/signal.scale
            min_encoded = (signal.minimum - signal.offset)/signal.scale
            
            if signal.is_float:
                pass
            elif signal.is_signed:
                negative_size = -(2**(signal.length-1)-1)
                if( max_encoded > total_size + negative_size):
                    header.write( "#error \"the maximum must fits the space alocated\"\n")
                    raise Exception(f"the maximum of {signal.name} in {message.name} must fits the space alocated, the encoded value is {max_encoded} and the maximum value to this space is {total_size+negative_size} (its a signed int)")
                if( min_encoded < negative_size ):
                    header.write( "#error \"the minimum must fits the space alocated\" \n")
                    raise Exception(f"the minimum of {signal.name} in {message.name} must  fits the space alocated, the encoded value is {min_encoded} and the maximum value to this space is {negative_size} (its a signed int)")
            else:
                if( max_encoded > total_size ):
                    header.write( "#error \"the maximum must fits the space alocated\"\n")
                    raise Exception(f"the maximum of {signal.name} in {message.name} must fits the space alocated, the encoded value is {max_encoded} and the maximum value to this space is {total_size}")
                if(  min_encoded < 0  ):
                    header.write( "#error \"the minimum must be equals or larger than 0\"\n")
                    raise Exception(f"the minimum of {signal.name} in {message.name} must be equals or larger than 0, the encoded value is {min_encoded}")

            if signal.choices:
                header.write(f"// Named Values to Signal: {signal.name}\n")
                for named_value in signal.choices:
                    header.write(f"#define CAN_VALUE_{signal.choices[named_value]} CAN_VALUE_{signal.choices[named_value]}\n")
                    header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_CAN_VALUE_{signal.choices[named_value]} {named_value}\n")
            
            header.write("\n")


    is_first = 1
    header.write("enum{\n")
    if there_is_msg_ext:
        header.write(f"    {source_file.upper()}_CAN_MSG_EXT_IN_INDEX=1,\n")
        is_first = 1
    if there_is_msg_std:
        if is_first:
            header.write(f"    {source_file.upper()}_CAN_MSG_STD_IN_INDEX=1,\n")
        else:
            header.write(f"    {source_file.upper()}_CAN_MSG_STD_IN_INDEX,\n")

    for message in dbc_inst.messages:
        if system_name in message.senders:
            header.write(f"    {source_file.upper()}_CAN_MSG_{message.name}_INDEX,\n")
    header.write(f"    {source_file.upper()}_CAN_MAX_MSG,\n")
    header.write("};\n\n")

    header.write("""typedef struct{
    uint32_t msg_id;
    uint32_t mask;
    CAN_MsgObjType msgType;
    uint32_t  flags;
    uint16_t  dlc;
}MessageProprieties_t;\n\n""")
    
    header.write(f"extern const MessageProprieties_t {source_file.lower()}_can_messages_proprieties[{source_file.upper()}_CAN_MAX_MSG];")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _PAYLOAD: payload arrived in the CAN \n")
    header.write( "//return VALUE: value decoded \n")
    header.write( "\n")
    header.write( "#define CAN_SIG_DECODE( _CAN_MSG , _CAN_SIG , _PAYLOAD ) \\\n")
    header.write( "( ( ( _CAN_MSG##_t *) &_PAYLOAD )->_CAN_SIG ) * ( (float) _CAN_MSG##_##_CAN_SIG##_SCALE) + _CAN_MSG##_##_CAN_SIG##_OFFSET\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _VALUE: the value to be encoded \n")
    header.write( "//return SIG_PAYLOAD: the value encoded \n")
    header.write( "\n")
    header.write( "#define CAN_SIG_ENCODE( _CAN_MSG , _CAN_SIG , _VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_TRANSMISSION_TYPE ) ( ( _VALUE - _CAN_MSG##_##_CAN_SIG##_OFFSET)/( (float) _CAN_MSG##_##_CAN_SIG##_SCALE ) )\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _VALUE: the value to be encoded \n")
    header.write( "//return IS_VALID: boolean informing if this value is valid\n")
    header.write( "\n")
    header.write( "#define CAN_SIG_IS_VALID( _CAN_MSG , _CAN_SIG , _VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_MINIMUM <= _VALUE ) && ( _VALUE <= _CAN_MSG##_##_CAN_SIG##_MAXIMUM)\n")
    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_VALUE: the name of the value with prefix CAN_VALUE \n")
    header.write( "//return VALUE: value of the named value\n")
    header.write( "\n")
    header.write( "#define CAN_GET_VALUE_BY_NAME( _CAN_MSG , _CAN_SIG , _CAN_VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_##_CAN_VALUE )\n")
    header.write("\n")
    header.write("#endif")
    header.write("\n")

    c_file = open(output_file_name + ".c", "w", encoding="utf-8")

    c_file.write( "/************************************************************/\n")
    c_file.write( "// Automatically generated C source file from CAN DBC file\n")
    c_file.write(f"// Source file name: {source_file}.dbc\n")
    c_file.write(f"// Date created: {datetime.now().strftime('%Y-%m-%d')}\n")
    c_file.write( "/************************************************************/\n")
    c_file.write( "\n")
    c_file.write( "\n")

    c_file.write(f"#include \"application.h\"\n")
    c_file.write(f"#include \"{source_file}.h\"\n")

    c_file.write(f"const MessageProprieties_t {source_file.lower()}_can_messages_proprieties[{source_file.upper()}_CAN_MAX_MSG] = ")
    c_file.write("{\n")

    if there_is_msg_std:
        c_file.write(f"    [{source_file.upper()}_CAN_MSG_STD_IN_INDEX] = "+"{")
        c_file.write(f"""
        .msg_id  = {receive_id_std},
        .mask    = {receive_mask_std},
        .msgType = CAN_MSG_OBJ_TYPE_RX,
        .flags   = CAN_MSG_OBJ_RX_INT_ENABLE|CAN_MSG_OBJ_USE_ID_FILTER,
        .dlc     = 8,
        """)
        c_file.write("    },\n")
    if there_is_msg_ext:
        c_file.write(f"    [{source_file.upper()}_CAN_MSG_EXT_IN_INDEX] = "+"{")
        c_file.write(f"""
        .msg_id  = {receive_id_ext},
        .mask    = {receive_mask_ext},
        .msgType = CAN_MSG_OBJ_TYPE_RX,
        .flags   = CAN_MSG_OBJ_RX_INT_ENABLE|CAN_MSG_OBJ_USE_EXT_FILTER|CAN_MSG_OBJ_USE_ID_FILTER,
        .dlc     = 8,
        """)
        c_file.write("    },\n")

    for message in dbc_inst.messages:
        if system_name in message.senders:
            c_file.write(f"    [{source_file.upper()}_CAN_MSG_{message.name}_INDEX] = ")
            c_file.write("{")
            c_file.write(f"""
        .msg_id = {source_file.upper()}_CAN_MSG_{message.name}_FRAME_ID,
        .mask   = 0x00000000,
        .msgType= CAN_MSG_OBJ_TYPE_TX,
        .flags  = CAN_MSG_OBJ_NO_FLAGS,
        .dlc    = 8,
""")
            c_file.write("    },\n")

    c_file.write("};\n")

    c_file.write( "\n")