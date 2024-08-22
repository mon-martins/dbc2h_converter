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
            
            # left to do type transmission diferetiation

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
            
            data_bit_position = signal.start
            data_length = signal.length
            data_endian = signal.byte_order

            byte_id = int(data_bit_position/8)
            byte_data_len = 8-data_bit_position%8

            if (data_endian == 'big_endian'):
                increment = -1
            elif (data_endian == 'little_endian'):
                increment = +1
            else:
                raise Exception(f"it wasn't possible to get the endianess of the signal")

            bits_to_concatenate = data_length

            concatenated_bits = 8-data_bit_position%8

            header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_GET_RAW_DATA(_CAN_RAW_DATA) \\\n")

            header.write(f"( ( _CAN_RAW_DATA.byte_{byte_id}) >> {data_bit_position%8} & {ones_bits_mask(concatenated_bits)} )")

            bits_to_concatenate -= concatenated_bits

            while(bits_to_concatenate>0):
                header.write(" | \\\n")
                byte_id += increment
                
                if (bits_to_concatenate > 8):
                    concatenated_bits = 8
                else:
                    concatenated_bits = bits_to_concatenate

                header.write(f" ( ( ( _CAN_RAW_DATA.byte_{byte_id}) & {ones_bits_mask(concatenated_bits)}) << {data_length-bits_to_concatenate} )")
                bits_to_concatenate -= concatenated_bits

            header.write("\n\n")


            byte_id = int(data_bit_position/8)
            byte_data_len = 8-data_bit_position%8

            if (data_endian == "big_endian"):
                increment = -1
            elif (data_endian == "little_endian"):
                increment = +1

            bits_to_concatenate = data_length

            concatenated_bits = 8-data_bit_position%8

            header.write(f"#define {source_file.upper()}_CAN_MSG_{message.name}_{source_file.upper()}_CAN_SIG_{signal.name}_GET_RAW_DATA( _CAN_RAW_DATA_TO_WRITE , _RAW_VALUE ) \\\n")

            header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} &= ({zeros_bits_mask(concatenated_bits,data_bit_position%8)}) \\\n")
            header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} |= ( ( _RAW_VALUE & {ones_bits_mask(concatenated_bits)} ) << {data_bit_position%8}) \\\n")

            bits_to_concatenate -= concatenated_bits
            while(bits_to_concatenate>0):
                byte_id += increment
                
                if (bits_to_concatenate > 8):
                    concatenated_bits = 8
                else:
                    concatenated_bits = bits_to_concatenate

                header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} &= {zeros_bits_mask(concatenated_bits)} \\\n")
                header.write(f"_CAN_RAW_DATA_TO_WRITE.byte_{byte_id} |= ( _RAW_VALUE >> {data_length-bits_to_concatenate}) & ({ones_bits_mask(concatenated_bits)}) \\\n")
                bits_to_concatenate -= concatenated_bits

            header.write("\n\n")



    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _ENCODED_VALUE: encoded value \n")
    header.write( "//return VALUE: value decoded \n")
    header.write( "\n")
    header.write( "#define CAN_SIG_DECODE( _CAN_MSG , _CAN_SIG , _ENCODED_VALUE ) \\\n")
    header.write( "( ( _ENCODED_VALUE ) * ( (float32_t) _CAN_MSG##_##_CAN_SIG##_SCALE) + _CAN_MSG##_##_CAN_SIG##_OFFSET\n")
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

    header.write( "\n")
    header.write( "\n")
    header.write( "//arg _CAN_MSG: the name of the message with prefix CAN_MSG_ \n")
    header.write( "//arg _CAN_SIG: the name of the signal  with prefix CAN_SIG_ \n")
    header.write( "//arg _CAN_VALUE: the name of the value with prefix CAN_VALUE \n")
    header.write( "//return VALUE: value of the named value\n")
    header.write( "\n")
    header.write( "#define CAN_GET_VALUE_BY_NAME( _CAN_MSG , _CAN_SIG , _CAN_VALUE ) \\\n")
    header.write( "( _CAN_MSG##_##_CAN_SIG##_##_CAN_VALUE )\n")


