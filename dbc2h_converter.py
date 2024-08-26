import cantools
from datetime import datetime

import sys
import os

def ones_bits_mask(num_of_one_bits:int, init_pos:int = 0):
    mask = "0b"
    bits = [7,6,5,4,3,2,1,0]
    for i in bits:
        if i < init_pos:
            mask += "0"
        elif i > init_pos+num_of_one_bits-1:
            mask += "0"
        else:
            mask += "1"
    return mask

def zeros_bits_mask(num_of_one_bits:int, init_pos:int = 0):
    mask = "0b"
    bits = [7,6,5,4,3,2,1,0]
    for i in bits:
        if i < init_pos:
            mask += "1"
        elif i > init_pos+num_of_one_bits-1:
            mask += "1"
        else:
            mask += "0"
    return mask

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

    header.write(f"#ifndef {source_file.upper()}_DBC_H_\n")
    header.write(f"#define {source_file.upper()}_DBC_H_")

    header.write("""
typedef struct{
    uint64_t byte_0:8;
    uint64_t byte_1:8;
    uint64_t byte_2:8;
    uint64_t byte_3:8;
    uint64_t byte_4:8;
    uint64_t byte_5:8;
    uint64_t byte_6:8;
    uint64_t byte_7:8;
}Can_Raw_Data_t;
"""

    )

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

        for signal in message.signals:
            header.write(f"// Signal: {signal.name}\n")
            header.write(f"#define {source_file.upper()}_CAN_SIG_{signal.name} {source_file.upper()}_CAN_SIG_{signal.name}\n")
            
            if signal.is_float:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE float\n")
            else:
                if signal.is_signed:
                    header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE int64_t\n")
                else:
                    header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_CAN_SIG_{signal.name}_TRANSMISSION_TYPE uint64_t\n")

            if signal.scale != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_SCALE {signal.scale}\n")
            else:
                header.write( "#error \"the scale must be a number\"\n")
                raise Exception(f"the scale of {signal.name} in {message.name} must be a number")
            
            if signal.offset != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_OFFSET {signal.offset}\n")
            else:
                header.write( "#error \"the offset must be a number\"\n")
                raise Exception(f"the offset of {signal.name} in {message.name} must be a number")

            if signal.minimum != None:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_MINIMUM {signal.minimum}\n")
            else:
                header.write( "#error \"the minimum must be a number\"\n")
                raise Exception(f"the minimum of {signal.name} in {message.name} must be a number")
            
            if signal.maximum != None and signal.maximum>signal.minimum:
                header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_MAXIMUM {signal.maximum}\n")
            else:
                header.write( "#error \"the maximum must be a number and larger than minimum\"\n")
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
                    header.write(f"#define {source_file.upper()}_CAN_VALUE_{signal.choices[named_value]} CAN_VALUE_{signal.choices[named_value]}\n")
                    header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_{source_file.upper()}_CAN_VALUE_{signal.choices[named_value]} {named_value}\n")
            


            data_length = signal.length
            data_endian = signal.byte_order

            if (data_endian == 'big_endian'):
                init_byte = int(signal.start/8)
                big_pos = 7 - (signal.start%8)
                end_pos_big = init_byte*8+big_pos+data_length-1
                end_byte = int(end_pos_big/8)
                data_bit_position = end_byte*8 + (7-end_pos_big%8)
                # print(data_bit_position)
            else:
                data_bit_position = signal.start

            byte_id = int(data_bit_position/8)

            if (data_endian == 'big_endian'):
                increment = -1
            elif (data_endian == 'little_endian'):
                increment = +1
            else:
                raise Exception(f"it wasn't possible to get the endianess of the signal")

            bits_to_concatenate = data_length
            
            concatenated_bits = min([bits_to_concatenate,8-data_bit_position%8])

            header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_GET_RAW_DATA(_CAN_RAW_DATA) \\\n")

            header.write(f"( ( _CAN_RAW_DATA.byte_{byte_id}) >> {data_bit_position%8} & {ones_bits_mask(concatenated_bits)} )")

            bits_to_concatenate -= concatenated_bits

            while(bits_to_concatenate>0):
                header.write(" | \\\n")
                byte_id += increment
                
                concatenated_bits = min([8,bits_to_concatenate])

                header.write(f" ( ( ( _CAN_RAW_DATA.byte_{byte_id}) & {ones_bits_mask(concatenated_bits)}) << {data_length-bits_to_concatenate} )")
                bits_to_concatenate -= concatenated_bits

            header.write("\n\n")


            byte_id = int(data_bit_position/8)

            bits_to_concatenate = data_length


            concatenated_bits = min([bits_to_concatenate,8-data_bit_position%8])

            header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_WRITE_RAW_DATA( _CAN_RAW_DATA_TO_WRITE , _RAW_VALUE ) \\\n")

            header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} &= ({zeros_bits_mask(concatenated_bits,data_bit_position%8)});\\\n")
            header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} |= ( ( _RAW_VALUE & {ones_bits_mask(concatenated_bits)} ) << {data_bit_position%8}); \\\n")

            bits_to_concatenate -= concatenated_bits
            while(bits_to_concatenate>0):
                byte_id += increment
                
                concatenated_bits = min([8,bits_to_concatenate])

                header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} &= {zeros_bits_mask(concatenated_bits)}; \\\n")
                header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} |= ( _RAW_VALUE >> {data_length-bits_to_concatenate}) & ({ones_bits_mask(concatenated_bits)}); \\\n")
                bits_to_concatenate -= concatenated_bits

            header.write("\n\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _ENCODED_VALUE: encoded value \n")
    header.write( "//return VALUE: value decoded \n")
    header.write( "\n")

    # Adapt to others transmission types
    # sugestion of separate functions to translate uint to a desired transmition type

    header.write( "#define CAN_SIG_DECODE( _CAN_MSG , _CAN_SIG , _ENCODED_VALUE ) \\\n")
    header.write( "( ( (uint64_t) _ENCODED_VALUE ) * ( (float32_t) _CAN_MSG##_##_CAN_SIG##_SCALE) + _CAN_MSG##_##_CAN_SIG##_OFFSET )\n")
    header.write( "\n")
    header.write( "\n")
    
    
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _VALUE: the value to be encoded \n")
    header.write( "//return SIG_PAYLOAD: the value encoded \n")
    header.write( "\n")

    # Adapt to others transmission types
    # sugestion of separate functions to translate a desired transmition type to a uint
     
    header.write( "#define CAN_SIG_ENCODE( _CAN_MSG , _CAN_SIG , _VALUE ) \\\n")
    header.write( "( uint64_t ) ( ( _VALUE - _CAN_MSG##_##_CAN_SIG##_OFFSET)/( (float) _CAN_MSG##_##_CAN_SIG##_SCALE ) )\n")

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

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_RAW_DATA: Can_Raw_Data_t with the message payload \n")
    header.write( "//return ENCODED_VALUE: value of the signal before decode\n")
    header.write( "\n")
    header.write( "#define CAN_GET_ENCODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_GET_RAW_DATA( _CAN_RAW_DATA ) )\n\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_RAW_DATA: Can_Raw_Data_t with the message payload \n")
    header.write( "//return DECODED_VALUE: value of the signal decoded\n")
    header.write( "\n")
    header.write( "#define CAN_GET_DECODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA ) \\\n")
    header.write( " CAN_SIG_DECODE(  _CAN_MSG , _CAN_SIG , CAN_GET_ENCODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA ) ) \n\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_RAW_DATA: Can_Raw_Data_t with the message payload \n")
    header.write( "//arg _ENCODED_VALUE: encoded Value to Set On Payload \n")
    header.write( "//return NONE")
    header.write( "\n")
    header.write( "#define CAN_WRITE_ENCODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA , _ENCODED_VALUE ) \\\n")
    header.write( "_CAN_MSG##_##_CAN_SIG##_WRITE_RAW_DATA( _CAN_RAW_DATA , _ENCODED_VALUE ) \n\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_RAW_DATA: Can_Raw_Data_t with the message payload \n")
    header.write( "//arg _DECODED_VALUE: decoded Value to Set On Payload \n")
    header.write( "//return NONE")
    header.write( "\n")
    header.write( "#define CAN_WRITE_DECODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA , _DECODED_VALUE ) \\\n")
    header.write( "CAN_WRITE_ENCODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA , CAN_SIG_ENCODE( _CAN_MSG , _CAN_SIG , _DECODED_VALUE ) ) \n\n")

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_RAW_DATA: Can_Raw_Data_t with the message payload \n")
    header.write( "//arg _NAMED_VALUE: Named Value to Set On Payload \n")
    header.write( "//return NONE")
    header.write( "\n")
    header.write( "#define CAN_WRITE_NAMED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA , _NAMED_VALUE ) \\\n")
    header.write( "CAN_WRITE_ENCODED_VALUE( _CAN_MSG , _CAN_SIG , _CAN_RAW_DATA ,  CAN_GET_VALUE_BY_NAME( _CAN_MSG , _CAN_SIG , _CAN_VALUE) ) \n\n")


#     header.write("""

# #ifndef CAN_COMMUNICATION_INT_TYPE
# #define CAN_COMMUNICATION_INT_TYPE int64_t
# #endif

# #ifndef CAN_COMMUNICATION_FLOAT_TYPE
# #define CAN_COMMUNICATION_FLOAT_TYPE float32_t
# #endif

# #ifndef CAN_COMMUNICATION_DOUBLE_TYPE
# #define CAN_COMMUNICATION_DOUBLE_TYPE float64_t
# #endif

# extern CAN_COMMUNICATION_INT_TYPE    value_cast_uint_to_int(uint64_t value, uint64_t length);
# extern CAN_COMMUNICATION_FLOAT_TYPE  value_cast_uint_to_float(uint64_t value, uint64_t length);
# extern CAN_COMMUNICATION_DOUBLE_TYPE value_cast_uint_to_double(uint64_t value, uint64_t length);
# """)

# MailBoxes

    header.write("enum{\n")

    header.write(f"    {source_file.upper()}_CAN_MSG_NONE_INDEX=0U,\n")

    if there_is_msg_ext:
        header.write(f"    {source_file.upper()}_CAN_MSG_EXT_IN_INDEX,\n")
    if there_is_msg_std:
        header.write(f"    {source_file.upper()}_CAN_MSG_STD_IN_INDEX,\n")

    for message in dbc_inst.messages:
        if system_name in message.senders:
            header.write(f"    {source_file.upper()}_CAN_MSG_{message.name}_INDEX,\n")
    header.write(f"    {source_file.upper()}_CAN_MAX_MSG,\n")
    header.write("};\n\n")

# C2000
# =============================================================================================================
# =============================================================================================================
# =============================================================================================================
    

    header.write("""typedef struct{
    uint32_t         msg_id;
    CAN_MsgFrameType frame_type;
    CAN_MsgObjType   msg_type;
    uint32_t         mask;
    uint32_t         flags;
    uint16_t         dlc;
}MessageProprieties_t;\n\n""")
    
    header.write(f"extern const MessageProprieties_t {source_file.lower()}_can_messages_proprieties[{source_file.upper()}_CAN_MAX_MSG];")




    c_file = open(output_file_name + ".c", "w", encoding="utf-8")

    c_file.write( "/************************************************************/\n")
    c_file.write( "// Automatically generated C source file from CAN DBC file\n")
    c_file.write(f"// Source file name: {source_file}.dbc\n")
    c_file.write(f"// Date created: {datetime.now().strftime('%Y-%m-%d')}\n")
    c_file.write( "/************************************************************/\n")
    c_file.write( "\n")
    c_file.write( "\n")

    c_file.write(f"#include \"{source_file}.h\"\n\n\n")

    c_file.write(f"const MessageProprieties_t {source_file.lower()}_can_messages_proprieties[{source_file.upper()}_CAN_MAX_MSG] = ")
    c_file.write("{\n")

    if there_is_msg_std:
        c_file.write(f"    [{source_file.upper()}_CAN_MSG_STD_IN_INDEX] = "+"{")
        c_file.write(f"""
        .msg_id     = {receive_id_std},
        .frame_type = CAN_MSG_FRAME_STD,
        .msg_type   = CAN_MSG_OBJ_TYPE_RX,
        .mask       = {receive_mask_std},
        .flags      = CAN_MSG_OBJ_RX_INT_ENABLE|CAN_MSG_OBJ_USE_ID_FILTER,
        .dlc        = 8,
        """)
        c_file.write("    },\n")
    if there_is_msg_ext:
        c_file.write(f"    [{source_file.upper()}_CAN_MSG_EXT_IN_INDEX] = "+"{")
        c_file.write(f"""
        .msg_id     = {receive_id_ext},
        .frame_type = CAN_MSG_FRAME_EXT,
        .msg_type   = CAN_MSG_OBJ_TYPE_RX,
        .mask       = {receive_mask_ext},
        .flags      = CAN_MSG_OBJ_RX_INT_ENABLE|CAN_MSG_OBJ_USE_EXT_FILTER|CAN_MSG_OBJ_USE_ID_FILTER,
        .dlc        = 8,
        """)
        c_file.write("    },\n")

    for message in dbc_inst.messages:
        if system_name in message.senders:
            if message.is_extended_frame:
                frame_type = "CAN_MSG_FRAME_EXT"
            else:
                frame_type = "CAN_MSG_FRAME_STD"
            c_file.write(f"    [{source_file.upper()}_CAN_MSG_{message.name}_INDEX] = ")
            c_file.write("{")
            c_file.write(f"""
        .msg_id = {source_file.upper()}_CAN_MSG_{message.name}_FRAME_ID,
        .frame_type = {frame_type},
        .msg_type= CAN_MSG_OBJ_TYPE_TX,
        .mask   = 0x00000000,
        .flags  = CAN_MSG_OBJ_NO_FLAGS,
        .dlc    = 8,
""")
            c_file.write("    },\n")

    c_file.write("};\n")

    c_file.write( "\n")

    header.write(f"\n\n#endif\n")
